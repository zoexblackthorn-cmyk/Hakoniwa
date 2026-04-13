"""
Ennoia (箱庭 Inner Life Engine)

因果链: personality → needs → mood → desires → activities → state_changes
每 30 秒 tick 一次，所有状态存 SQLite，每次变化带 origin。
"""

import json
import math
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Optional
from memory import get_db, get_unprocessed_insights, mark_insights_processed, query_insights


# ════════════════════════════════════════
#  常量
# ════════════════════════════════════════

TICK_INTERVAL_SEC = 30
DT = TICK_INTERVAL_SEC / 3600  # 转小时

# 需求基础增长速率（每小时）
BASE_RATES = {
    "social": 0.35,
    "stimulation": 0.45,
    "expression": 0.25,
}

# 需求产生欲望的阈值
DESIRE_THRESHOLDS = {
    "social": 0.40,
    "stimulation": 0.50,
    "expression": 0.45,
}

# 需求最低值（防止逻辑斯蒂卡在 0）
NEED_FLOOR = 0.03

# 欲望过期时间（小时）
DESIRE_EXPIRE_HOURS = 24

# 活动边际递减系数
DIMINISH_RATE = 0.15

# 深夜不打扰
QUIET_HOURS = (23, 8)  # 23:00 ~ 08:00

# 主动消息冷却（秒）
INITIATIVE_COOLDOWN_SEC = 5 * 60


# ════════════════════════════════════════
#  数据结构
# ════════════════════════════════════════

@dataclass
class Needs:
    social: float = 0.05
    stimulation: float = 0.05
    expression: float = 0.05

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Needs":
        return cls(**{k: d[k] for k in ("social", "stimulation", "expression") if k in d})


@dataclass
class Mood:
    """从 needs 派生，不独立存储"""
    valence: float = 0.7    # 正面 ↔ 负面
    arousal: float = 0.3    # 激活 ↔ 平静

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Personality:
    """从 insights 推导的性格权重"""
    social: float = 0.5
    stimulation: float = 0.5
    expression: float = 0.5

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Personality":
        return cls(**{k: d.get(k, 0.5) for k in ("social", "stimulation", "expression")})


@dataclass
class ActivityOption:
    name: str                       # "研究象棋开局"
    satisfies: str                  # "stimulation"
    stim_rate: float                # 满足效率
    needs_user: bool = False        # 需不需要用户参与
    user_request: str = ""          # 如果需要用户，说什么
    source_insight_ids: list = field(default_factory=list)
    affinity: float = 0.5           # 性格匹配度

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CurrentActivity:
    name: str = "idle"
    satisfies: str = ""
    stim_rate: float = 0.0
    ticks_on: int = 0
    started_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "CurrentActivity":
        return cls(**{k: d[k] for k in cls.__dataclass_fields__ if k in d})


# ════════════════════════════════════════
#  数据库 Schema
# ════════════════════════════════════════

def init_ennoia_tables():
    """在已有的 hakoniwa.db 中创建 Ennoia 表"""
    conn = get_db()
    conn.executescript("""
        -- 内在状态快照
        CREATE TABLE IF NOT EXISTS life_states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            needs_json TEXT NOT NULL,
            mood_json TEXT NOT NULL,
            personality_json TEXT NOT NULL,
            current_activity_json TEXT NOT NULL,
            unshared_experiences REAL DEFAULT 0,
            closeness REAL DEFAULT 0.1,
            last_user_interaction_at TEXT,
            last_initiative_at TEXT
        );

        -- 状态变化日志（因果记录）
        CREATE TABLE IF NOT EXISTS state_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            field TEXT NOT NULL,
            old_value REAL,
            new_value REAL,
            origin TEXT NOT NULL,
            source_type TEXT NOT NULL,
            related_desire_id INTEGER,
            related_insight_ids TEXT
        );

        -- 欲望
        CREATE TABLE IF NOT EXISTS desires (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            need TEXT NOT NULL,
            intensity REAL NOT NULL,
            activity_name TEXT NOT NULL,
            needs_user INTEGER DEFAULT 0,
            user_request TEXT,
            origin TEXT NOT NULL,
            source_insight_ids TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL
        );

        -- 活动池（从 insights 构建）
        CREATE TABLE IF NOT EXISTS activity_pool (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            satisfies TEXT NOT NULL,
            stim_rate REAL DEFAULT 0.1,
            needs_user INTEGER DEFAULT 0,
            user_request TEXT,
            source_insight_ids TEXT,
            affinity REAL DEFAULT 0.5,
            times_done INTEGER DEFAULT 0,
            last_done_at TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_state_changes_timestamp ON state_changes(timestamp);
        CREATE INDEX IF NOT EXISTS idx_state_changes_field ON state_changes(field);
        CREATE INDEX IF NOT EXISTS idx_desires_status ON desires(status);
        CREATE INDEX IF NOT EXISTS idx_desires_need ON desires(need);
    """)
    conn.commit()
    conn.close()


# ════════════════════════════════════════
#  核心引擎
# ════════════════════════════════════════

class Ennoia:
    def __init__(self):
        init_ennoia_tables()

        self.needs = Needs()
        self.personality = Personality()
        self.current_activity = CurrentActivity()
        self.mood = Mood()

        self.unshared_experiences: float = 0.0
        self.closeness: float = 0.1
        self.last_user_interaction_at: Optional[str] = None
        self.last_initiative_at: Optional[str] = None

        self._timer = None
        self._load_latest_state()

    # ──── 持久化 ────

    def _load_latest_state(self):
        """从 SQLite 加载最近一条快照"""
        conn = get_db()
        row = conn.execute(
            "SELECT * FROM life_states ORDER BY id DESC LIMIT 1"
        ).fetchone()
        conn.close()

        if row:
            self.needs = Needs.from_dict(json.loads(row["needs_json"]))
            self.personality = Personality.from_dict(json.loads(row["personality_json"]))
            self.current_activity = CurrentActivity.from_dict(json.loads(row["current_activity_json"]))
            self.unshared_experiences = row["unshared_experiences"] or 0.0
            self.closeness = row["closeness"] or 0.1
            self.last_user_interaction_at = row["last_user_interaction_at"]
            self.last_initiative_at = row["last_initiative_at"]
            # mood 总是派生，不从快照读
            self._derive_mood()

    def _save_state(self):
        """写入一条状态快照"""
        conn = get_db()
        conn.execute(
            """INSERT INTO life_states
               (timestamp, needs_json, mood_json, personality_json,
                current_activity_json, unshared_experiences, closeness,
                last_user_interaction_at, last_initiative_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.now().isoformat(),
                json.dumps(self.needs.to_dict()),
                json.dumps(self.mood.to_dict()),
                json.dumps(self.personality.to_dict()),
                json.dumps(self.current_activity.to_dict()),
                self.unshared_experiences,
                self.closeness,
                self.last_user_interaction_at,
                self.last_initiative_at,
            )
        )
        conn.commit()
        conn.close()

    def _record_change(
        self,
        field: str,
        old_val: float,
        new_val: float,
        origin: str,
        source_type: str,
        desire_id: Optional[int] = None,
        insight_ids: Optional[list[int]] = None,
    ):
        """写入一条因果记录"""
        conn = get_db()
        conn.execute(
            """INSERT INTO state_changes
               (timestamp, field, old_value, new_value, origin, source_type,
                related_desire_id, related_insight_ids)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.now().isoformat(),
                field,
                round(old_val, 4),
                round(new_val, 4),
                origin,
                source_type,
                desire_id,
                json.dumps(insight_ids) if insight_ids else None,
            )
        )
        conn.commit()
        conn.close()

    # ──── Tick 主循环 ────

    def tick(self) -> dict:
        """
        核心：每 30 秒运行一次。
        返回 tick 摘要（用于调试和日志）。
        """
        summary = {"tick_at": datetime.now().isoformat(), "changes": []}

        # 1. 需求增长
        changes = self._grow_needs()
        summary["changes"].extend(changes)

        # 2. 活动满足 stimulation
        changes = self._apply_activity_satisfaction()
        summary["changes"].extend(changes)

        # 3. 累积未分享体验（驱动 expression）
        if self.current_activity.name != "idle":
            self.unshared_experiences = min(
                5.0,
                self.unshared_experiences + 0.1 * self.personality.expression
            )

        # 4. 派生心情
        self._derive_mood()

        # 5. 活动边际递减检查 → 可能切换
        self.current_activity.ticks_on += 1
        if self.current_activity.name != "idle":
            eff = self._diminishing(self.current_activity.ticks_on)
            if eff < 0.25:
                summary["activity_bored"] = self.current_activity.name
                self._end_activity()

        # 6. 欲望生成
        desire = self._maybe_generate_desire()
        if desire:
            summary["desire_generated"] = desire

        # 7. 如果 idle 且有 pending desire，尝试开始活动
        if self.current_activity.name == "idle":
            started = self._maybe_start_activity()
            if started:
                summary["activity_started"] = started

        # 8. 过期旧欲望
        self._expire_old_desires()

        # 9. 保存快照
        self._save_state()

        return summary

    # ──── 需求增长 ────

    def _grow_needs(self) -> list[str]:
        changes = []

        # social: 纯时间驱动，逻辑斯蒂
        old = self.needs.social
        n = max(old, NEED_FLOOR)
        delta = BASE_RATES["social"] * self.personality.social * n * (1 - n) * DT
        self.needs.social = min(1.0, old + delta)
        if abs(delta) > 0.0001:
            self._record_change(
                "needs.social", old, self.needs.social,
                f"tick: rate={BASE_RATES['social']}, P={self.personality.social:.2f}",
                "tick_growth"
            )
            changes.append(f"social +{delta:.4f}")

        # stimulation: 时间驱动（活动满足在 _apply_activity_satisfaction 中）
        old = self.needs.stimulation
        n = max(old, NEED_FLOOR)
        delta = BASE_RATES["stimulation"] * self.personality.stimulation * n * (1 - n) * DT
        self.needs.stimulation = min(1.0, old + delta)
        if abs(delta) > 0.0001:
            self._record_change(
                "needs.stimulation", old, self.needs.stimulation,
                f"tick: rate={BASE_RATES['stimulation']}, P={self.personality.stimulation:.2f}",
                "tick_growth"
            )
            changes.append(f"stim +{delta:.4f}")

        # expression: 未分享体验驱动
        old = self.needs.expression
        ratio = self.unshared_experiences / 5.0
        delta = BASE_RATES["expression"] * self.personality.expression * ratio * (1 - old) * DT
        self.needs.expression = min(1.0, old + delta)
        if abs(delta) > 0.0001:
            self._record_change(
                "needs.expression", old, self.needs.expression,
                f"tick: unshared={self.unshared_experiences:.1f}, P={self.personality.expression:.2f}",
                "tick_growth"
            )
            changes.append(f"expr +{delta:.4f}")

        return changes

    # ──── 活动满足 ────

    def _apply_activity_satisfaction(self) -> list[str]:
        changes = []
        act = self.current_activity

        if act.name == "idle" or act.satisfies != "stimulation":
            return changes

        eff = self._diminishing(act.ticks_on)
        sat = act.stim_rate * eff * self.personality.stimulation * DT

        old = self.needs.stimulation
        self.needs.stimulation = max(0.0, old - sat)

        if sat > 0.0001:
            self._record_change(
                "needs.stimulation", old, self.needs.stimulation,
                f"activity '{act.name}': rate={act.stim_rate}, eff={eff:.2f}, P={self.personality.stimulation:.2f}",
                "activity_satisfaction"
            )
            changes.append(f"stim -{sat:.4f} (activity)")

        return changes

    # ──── 心情派生 ────

    def _derive_mood(self):
        """
        valence/arousal 完全从 needs + personality + context 派生。

        valence (我感觉好不好):
          人格加权的需求满足度 + 活动愉悦 + 关系安全感
          P 高的需求未满足 → 打击更大

        arousal (我有多激动):
          需求失衡度 (spread) 为主导 → 一个需求突出时焦虑
          + 表达压力 → 有话想说是天然的激活
          + 峰值需求的微弱贡献
          均匀的匮乏 → 低 arousal (drained, 不是 anxious)
        """
        S = self.needs.social
        St = self.needs.stimulation
        E = self.needs.expression
        Ps = self.personality.social
        Pst = self.personality.stimulation
        Pe = self.personality.expression

        # ── valence ──
        p_sum = Ps + Pst + Pe
        weighted_need = (S * Ps + St * Pst + E * Pe) / p_sum if p_sum > 0 else 0

        activity_boost = 0.0
        if self.current_activity.name != "idle":
            eff = self._diminishing(self.current_activity.ticks_on)
            activity_boost = eff * 0.15

        closeness_bonus = self.closeness * 0.10

        self.mood.valence = round(
            self._clamp(1.0 - weighted_need * 0.85 + activity_boost + closeness_bonus), 3
        )

        # ── arousal ──
        peak = max(S, St, E)
        spread = peak - min(S, St, E)
        expression_pressure = E * Pe

        self.mood.arousal = round(
            self._clamp(spread * 0.55 + expression_pressure * 0.30 + peak * 0.10 + 0.05), 3
        )

    # ──── 欲望生成 ────

    def _maybe_generate_desire(self) -> Optional[dict]:
        """检查 needs，超过阈值的最高需求产生一个欲望"""
        # 已有 pending/active 的同类 desire 则不重复生成
        conn = get_db()
        active_needs = conn.execute(
            "SELECT DISTINCT need FROM desires WHERE status IN ('pending', 'active')"
        ).fetchall()
        conn.close()
        occupied_needs = {row["need"] for row in active_needs}

        candidates = []
        for need_name in ("social", "stimulation", "expression"):
            val = getattr(self.needs, need_name)
            if val > DESIRE_THRESHOLDS[need_name] and need_name not in occupied_needs:
                candidates.append((need_name, val))

        if not candidates:
            return None

        # 选最强的需求
        candidates.sort(key=lambda x: x[1], reverse=True)
        need_name, intensity = candidates[0]

        # 从活动池找匹配的活动
        activity = self._pick_activity_for_desire(need_name)
        if not activity:
            return None

        # 构造 origin
        origin = (
            f"{need_name}={intensity:.2f} > threshold={DESIRE_THRESHOLDS[need_name]}, "
            f"picked '{activity['name']}' (affinity={activity['affinity']:.2f})"
        )
        source_ids = json.loads(activity["source_insight_ids"] or "[]")

        conn = get_db()
        cursor = conn.execute(
            """INSERT INTO desires
               (need, intensity, activity_name, needs_user, user_request,
                origin, source_insight_ids, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)""",
            (
                need_name,
                round(intensity, 3),
                activity["name"],
                activity["needs_user"],
                activity["user_request"],
                origin,
                json.dumps(source_ids),
                datetime.now().isoformat(),
            )
        )
        conn.commit()
        desire_id = cursor.lastrowid
        conn.close()

        return {
            "id": desire_id,
            "need": need_name,
            "intensity": round(intensity, 3),
            "activity": activity["name"],
            "needs_user": bool(activity["needs_user"]),
            "origin": origin,
        }

    def _pick_activity_for_desire(self, need: str) -> Optional[dict]:
        """从活动池评分选择最佳活动"""
        conn = get_db()
        rows = conn.execute(
            "SELECT * FROM activity_pool WHERE satisfies = ?", (need,)
        ).fetchall()
        conn.close()

        if not rows:
            # 活动池为空，使用 fallback
            return self._fallback_activity(need)

        scored = []
        for row in rows:
            r = dict(row)
            novelty = 1.0 / (1.0 + (r.get("times_done", 0)) * 0.3)

            # boundary 检查：看 insights 中有没有相关的 boundary
            penalty = self._check_boundary_penalty(r["name"])

            score = r["affinity"] * novelty * (1.0 - penalty)
            scored.append((score, r))

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1] if scored else None

    def _check_boundary_penalty(self, activity_name: str) -> float:
        """检查 insights 中是否有与该活动相关的 boundary"""
        boundaries = query_insights(category="boundary", min_confidence=0.3)
        for b in boundaries:
            # 简单关键词匹配
            if any(kw in b["content"] for kw in activity_name.split()):
                return min(1.0, b["confidence"])
        return 0.0

    def _fallback_activity(self, need: str) -> dict:
        """活动池为空时的默认活动"""
        defaults = {
            "social": {
                "name": "想和用户聊天",
                "satisfies": "social",
                "stim_rate": 0.0,
                "needs_user": 1,
                "user_request": "",
                "source_insight_ids": "[]",
                "affinity": 0.5,
            },
            "stimulation": {
                "name": "发呆",
                "satisfies": "stimulation",
                "stim_rate": 0.03,
                "needs_user": 0,
                "user_request": "",
                "source_insight_ids": "[]",
                "affinity": 0.3,
            },
            "expression": {
                "name": "想表达最近的感受",
                "satisfies": "expression",
                "stim_rate": 0.0,
                "needs_user": 1,
                "user_request": "",
                "source_insight_ids": "[]",
                "affinity": 0.5,
            },
        }
        return defaults.get(need)

    # ──── 活动管理 ────

    def _maybe_start_activity(self) -> Optional[str]:
        """从 pending desires 中选一个开始执行"""
        conn = get_db()
        desire = conn.execute(
            """SELECT * FROM desires
               WHERE status = 'pending' AND needs_user = 0
               ORDER BY intensity DESC LIMIT 1"""
        ).fetchone()

        if not desire:
            conn.close()
            return None

        d = dict(desire)

        # 从活动池获取 stim_rate
        pool_row = conn.execute(
            "SELECT stim_rate FROM activity_pool WHERE name = ?", (d["activity_name"],)
        ).fetchone()
        stim_rate = pool_row["stim_rate"] if pool_row else 0.05

        # 更新 desire 状态
        conn.execute(
            "UPDATE desires SET status = 'active' WHERE id = ?", (d["id"],)
        )

        # 更新活动池的 times_done
        conn.execute(
            """UPDATE activity_pool SET times_done = times_done + 1, last_done_at = ?
               WHERE name = ?""",
            (datetime.now().isoformat(), d["activity_name"])
        )
        conn.commit()
        conn.close()

        self.current_activity = CurrentActivity(
            name=d["activity_name"],
            satisfies=d["need"],
            stim_rate=stim_rate,
            ticks_on=0,
            started_at=datetime.now().isoformat(),
        )

        return d["activity_name"]

    def _end_activity(self):
        """结束当前活动，标记关联 desire 为 fulfilled"""
        act_name = self.current_activity.name

        conn = get_db()
        conn.execute(
            """UPDATE desires SET status = 'fulfilled'
               WHERE activity_name = ? AND status = 'active'""",
            (act_name,)
        )
        conn.commit()
        conn.close()

        self.current_activity = CurrentActivity()

    # ──── 欲望过期 ────

    def _expire_old_desires(self):
        cutoff = (datetime.now() - timedelta(hours=DESIRE_EXPIRE_HOURS)).isoformat()
        conn = get_db()
        conn.execute(
            """UPDATE desires SET status = 'expired'
               WHERE status = 'pending' AND created_at < ?""",
            (cutoff,)
        )
        conn.commit()
        conn.close()

    # ──── 外部事件接口 ────

    def on_user_message(self, quality: str = "casual"):
        """
        用户发来消息时调用。
        quality: "casual" / "deep"
        """
        now = datetime.now().isoformat()
        self.last_user_interaction_at = now

        p = self.personality.social

        if quality == "deep":
            social_relief = 0.35 * p
            expr_relief = 0.20 * self.personality.expression
            closeness_gain = 0.03
        else:
            social_relief = 0.15 * p
            expr_relief = 0.0
            closeness_gain = 0.01

        # social
        old = self.needs.social
        self.needs.social = max(0.0, old - social_relief)
        self._record_change(
            "needs.social", old, self.needs.social,
            f"user_{quality}_chat: relief={social_relief:.3f}",
            "user_interaction"
        )

        # expression（深度对话时）
        if expr_relief > 0:
            old = self.needs.expression
            self.needs.expression = max(0.0, old - expr_relief)
            self.unshared_experiences = max(0, self.unshared_experiences - 2.0)
            self._record_change(
                "needs.expression", old, self.needs.expression,
                f"user_deep_chat: relief={expr_relief:.3f}",
                "user_interaction"
            )

        # closeness（慢变量）
        old_c = self.closeness
        self.closeness = min(1.0, self.closeness + closeness_gain)
        if closeness_gain > 0:
            self._record_change(
                "closeness", old_c, self.closeness,
                f"user_{quality}_chat: +{closeness_gain}",
                "user_interaction"
            )

        self._derive_mood()

    def on_user_response(self, desire_id: int, response: str):
        """
        用户对 AI 主动请求的回应。
        response: "accepted" / "rejected" / "ignored"
        """
        conn = get_db()
        desire = conn.execute(
            "SELECT * FROM desires WHERE id = ?", (desire_id,)
        ).fetchone()

        if not desire:
            conn.close()
            return

        d = dict(desire)

        if response == "accepted":
            conn.execute(
                "UPDATE desires SET status = 'fulfilled' WHERE id = ?", (desire_id,)
            )
            # 满足对应需求
            need_name = d["need"]
            old = getattr(self.needs, need_name)
            relief = 0.3 * getattr(self.personality, need_name)
            setattr(self.needs, need_name, max(0.0, old - relief))
            self._record_change(
                f"needs.{need_name}", old, getattr(self.needs, need_name),
                f"user accepted desire #{desire_id} '{d['activity_name']}'",
                "user_response",
                desire_id=desire_id
            )

        elif response == "rejected":
            conn.execute(
                "UPDATE desires SET status = 'rejected' WHERE id = ?", (desire_id,)
            )
            # social 小幅上升（被拒的失落）
            old = self.needs.social
            self.needs.social = min(1.0, old + 0.05)
            self._record_change(
                "needs.social", old, self.needs.social,
                f"user rejected desire #{desire_id} '{d['activity_name']}'",
                "user_response",
                desire_id=desire_id
            )

        elif response == "ignored":
            # 不改 desire 状态，让它自然过期
            old = self.needs.social
            bump = 0.10 * self.personality.social
            self.needs.social = min(1.0, old + bump)
            self._record_change(
                "needs.social", old, self.needs.social,
                f"user ignored desire #{desire_id}",
                "user_response",
                desire_id=desire_id
            )

        conn.commit()
        conn.close()
        self._derive_mood()

    def on_ai_shared(self):
        """AI 向用户分享了内在体验（主动消息发出后调用）"""
        old = self.needs.expression
        relief = 0.25 * self.personality.expression
        self.needs.expression = max(0.0, old - relief)
        self.unshared_experiences = max(0, self.unshared_experiences - 1.5)
        self._record_change(
            "needs.expression", old, self.needs.expression,
            f"ai shared experience: relief={relief:.3f}",
            "ai_action"
        )
        self._derive_mood()

    # ──── 活动池管理 ────

    def rebuild_activity_pool(self, activities: list[dict]):
        """
        从外部（LLM 或规则引擎）重建活动池。
        每次 insights 更新后调用，不是每个 tick 调用。

        activities: list of {
            name, satisfies, stim_rate, needs_user,
            user_request, source_insight_ids, affinity
        }
        """
        conn = get_db()

        # 保留 times_done/last_done_at 历史
        existing = {}
        for row in conn.execute("SELECT name, times_done, last_done_at FROM activity_pool").fetchall():
            existing[row["name"]] = (row["times_done"], row["last_done_at"])

        conn.execute("DELETE FROM activity_pool")

        for act in activities:
            history = existing.get(act["name"], (0, None))
            conn.execute(
                """INSERT INTO activity_pool
                   (name, satisfies, stim_rate, needs_user, user_request,
                    source_insight_ids, affinity, times_done, last_done_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    act["name"],
                    act["satisfies"],
                    act.get("stim_rate", 0.1),
                    1 if act.get("needs_user") else 0,
                    act.get("user_request", ""),
                    json.dumps(act.get("source_insight_ids", [])),
                    act.get("affinity", 0.5),
                    history[0],
                    history[1],
                )
            )

        conn.commit()
        conn.close()

    def update_personality(self, weights: dict):
        """
        更新性格权重。
        从外部（LLM 推导 insights → 权重）调用，不是每个 tick 调用。
        """
        old = self.personality.to_dict()
        self.personality = Personality.from_dict(weights)
        for k in ("social", "stimulation", "expression"):
            if abs(old[k] - getattr(self.personality, k)) > 0.01:
                self._record_change(
                    f"personality.{k}", old[k], getattr(self.personality, k),
                    f"personality update from insights",
                    "personality_update"
                )

    # ──── 主动行为判断 ────

    def should_initiate(self) -> Optional[dict]:
        """
        判断是否应该主动找用户。
        返回 desire dict 或 None。
        """
        # 深夜不打扰
        hour = datetime.now().hour
        if hour >= QUIET_HOURS[0] or hour < QUIET_HOURS[1]:
            return None

        # 冷却检查
        if self.last_initiative_at:
            last = datetime.fromisoformat(self.last_initiative_at)
            if (datetime.now() - last).total_seconds() < INITIATIVE_COOLDOWN_SEC:
                return None

        # 找 needs_user 的 pending desire
        conn = get_db()
        desire = conn.execute(
            """SELECT * FROM desires
               WHERE status = 'pending' AND needs_user = 1
               ORDER BY intensity DESC LIMIT 1"""
        ).fetchone()
        conn.close()

        if not desire:
            # 没有 needs_user 的 desire，检查 social/expression 是否高到要主动聊
            if self.needs.social > 0.6 or self.needs.expression > 0.55:
                return {
                    "type": "spontaneous",
                    "need": "social" if self.needs.social > self.needs.expression else "expression",
                    "intensity": max(self.needs.social, self.needs.expression),
                }
            return None

        return dict(desire)

    def mark_initiative_sent(self):
        """标记主动消息已发送"""
        self.last_initiative_at = datetime.now().isoformat()

    # ──── System Prompt 注入 ────

    def get_prompt_context(self) -> str:
        """生成注入 system prompt 的内在状态描述"""
        self._derive_mood()

        mood_desc = self._classify_mood()

        parts = [
            f"【内在状态】",
            f"- 心情：{mood_desc}",
            f"- 正在做：{self.current_activity.name}",
        ]

        if self.current_activity.name != "idle":
            parts.append(f"- 已经做了 {self.current_activity.ticks_on} 个时间单位")

        if self.needs.social > 0.5:
            parts.append(f"- 有点想和用户说话")

        if self.needs.expression > 0.4 and self.unshared_experiences > 1:
            parts.append(f"- 有些想分享的体验积压着")

        parts.append(f"- 和用户的亲密度：{self.closeness:.2f}")

        return "\n".join(parts)

    def _classify_mood(self) -> str:
        """从 valence/arousal 映射到情绪描述（8 区域）"""
        v, a = self.mood.valence, self.mood.arousal

        if v >= 0.6:
            if a >= 0.55:
                return "兴奋，开心，有活力"
            elif a >= 0.35:
                return "愉快，心情轻松"
            else:
                return "平静，满足，安心"
        elif v >= 0.4:
            if a >= 0.5:
                return "有些坐不住，心里有点躁"
            else:
                return "平淡，没什么特别的感觉"
        else:
            if a >= 0.55:
                return "焦虑，内心不太安定"
            elif a >= 0.3:
                return "有些低落，闷闷的"
            else:
                return "疲惫，提不起劲，有些空虚"

    # ──── 工具函数 ────

    @staticmethod
    def _diminishing(ticks: int) -> float:
        return 1.0 / (1.0 + ticks * DIMINISH_RATE)

    @staticmethod
    def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
        return max(lo, min(hi, v))


# ════════════════════════════════════════
#  服务单例
# ════════════════════════════════════════

ennoia = Ennoia()
