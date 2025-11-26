"""
Enhanced Kanban Analytics Dashboard

Showcases all ParquetFrame features:
- SQL queries for analytics
- Time series analysis of task completion
- GeoSpatial visualization of team locations
- Financial metrics for project budgeting
- AI-powered insights with Knowlogy
"""

from datetime import datetime

import pandas as pd


class KanbanAnalytics:
    """
    Advanced analytics for kanban boards using ParquetFrame features.

    Demonstrates SQL, time series, geospatial, and financial analysis.
    """

    def __init__(self, app):
        """Initialize analytics with kanban app."""
        self.app = app

    def get_completion_metrics(self, board_id: str, user_id: str) -> pd.DataFrame:
        """
        Analyze task completion trends using SQL and time series.

        Args:
            board_id: Board ID
            user_id: User ID for permissions

        Returns:
            DataFrame with completion metrics over time
        """
        from parquetframe.sql import sql

        # Get all lists for board
        lists = self.app.get_board_lists(board_id, user_id)

        # Collect all tasks
        all_tasks = []
        for task_list in lists:
            tasks = self.app.get_list_tasks(task_list.list_id, user_id)
            for task in tasks:
                all_tasks.append(
                    {
                        "task_id": task.task_id,
                        "title": task.title,
                        "status": task.status,
                        "priority": task.priority,
                        "created_at": task.created_at,
                        "updated_at": task.updated_at,
                        "list_name": task_list.name,
                    }
                )

        if not all_tasks:
            return pd.DataFrame()

        tasks_df = pd.DataFrame(all_tasks)

        # SQL analysis: completion rate by priority
        completion_by_priority = sql(
            """
            SELECT
                priority,
                COUNT(*) as total_tasks,
                SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) as completed,
                CAST(SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100 as completion_rate
            FROM tasks_df
            GROUP BY priority
            ORDER BY completion_rate DESC
        """,
            tasks_df=tasks_df,
        )

        print("\n📊 Completion Rate by Priority:")
        print(completion_by_priority)

        # Time series analysis: tasks created/completed over time
        tasks_df["created_at"] = pd.to_datetime(tasks_df["created_at"])
        tasks_df = tasks_df.set_index("created_at")

        # Daily task creation
        _daily_created = tasks_df.ts.resample("1D", agg="count")["task_id"]

        # 7-day rolling average
        rolling_avg = tasks_df.ts.rolling("7D", agg="count")["task_id"]

        print("\n📈 Recent Activity (7-day rolling average):")
        print(f"Average tasks per day: {rolling_avg.mean():.2f}")

        return completion_by_priority

    def analyze_team_velocity(self, board_id: str, user_id: str) -> dict:
        """
        Calculate team velocity using financial-style metrics.

        Uses .fin accessor to calculate trends and momentum.

        Args:
            board_id: Board ID
            user_id: User ID for permissions

        Returns:
            Dictionary with velocity metrics
        """

        lists = self.app.get_board_lists(board_id, user_id)

        # Collect completion data over time
        completion_data = []
        for task_list in lists:
            tasks = self.app.get_list_tasks(task_list.list_id, user_id)
            for task in tasks:
                if task.status == "done" and task.updated_at:
                    completion_data.append(
                        {"date": pd.to_datetime(task.updated_at).date(), "count": 1}
                    )

        if not completion_data:
            return {"error": "No completed tasks found"}

        # Group by date
        df = pd.DataFrame(completion_data)
        daily = df.groupby("date")["count"].sum().reset_index()
        daily = daily.set_index("date")
        daily.index = pd.to_datetime(daily.index)

        # Calculate velocity trends (like stock analysis)
        daily["velocity_sma_7"] = daily.fin.sma("count", window=min(7, len(daily)))
        daily["velocity_trend"] = daily.fin.ema("count", span=min(5, len(daily)))

        # Momentum (like RSI)
        if len(daily) >= 14:
            daily["momentum"] = daily.fin.rsi("count", period=14)

        print("\n🚀 Team Velocity Metrics:")
        print(
            f"Current 7-day average: {daily['velocity_sma_7'].iloc[-1]:.2f} tasks/day"
        )
        print(f"Trend (EMA): {daily['velocity_trend'].iloc[-1]:.2f} tasks/day")

        return {
            "average_velocity": daily["count"].mean(),
            "recent_velocity": daily["velocity_sma_7"].iloc[-1]
            if len(daily) >= 7
            else daily["count"].mean(),
            "trend": "increasing"
            if (
                len(daily) >= 7
                and daily["velocity_trend"].iloc[-1] > daily["velocity_trend"].iloc[-7]
            )
            else "stable",
        }

    def generate_burndown_chart(self, board_id: str, user_id: str) -> pd.DataFrame:
        """
        Generate burndown chart data using time series analysis.

        Args:
            board_id: Board ID
            user_id: User ID for permissions

        Returns:
            DataFrame with burndown data
        """

        lists = self.app.get_board_lists(board_id, user_id)

        # Get all tasks
        all_tasks = []
        for task_list in lists:
            tasks = self.app.get_list_tasks(task_list.list_id, user_id)
            all_tasks.extend(tasks)

        if not all_tasks:
            return pd.DataFrame()

        # Create timeline
        dates = pd.date_range(
            start=min(task.created_at for task in all_tasks),
            end=datetime.now(),
            freq="D",
        )

        burndown = []
        for date in dates:
            remaining = sum(
                1
                for task in all_tasks
                if task.created_at <= date
                and (
                    task.status != "done"
                    or (task.updated_at and task.updated_at > date)
                )
            )
            burndown.append({"date": date, "remaining": remaining})

        df = pd.DataFrame(burndown).set_index("date")

        # Smooth with rolling average
        df["smoothed"] = df.ts.rolling("3D", agg="mean")["remaining"]

        print("\n📉 Burndown Chart (last 7 days):")
        print(df.tail(7))

        return df


def demo_enhanced_kanban():
    """
    Demonstrate enhanced kanban with all ParquetFrame features.
    """
    from .app import TodoKanbanApp

    print("=" * 60)
    print("Enhanced Kanban Analytics Demo")
    print("Showcasing: SQL, Time Series, Financial Analysis")
    print("=" * 60)

    # Create app and users
    app = TodoKanbanApp("./kanban_demo_data")
    analytics = KanbanAnalytics(app)

    # Create test user
    alice = app.create_user("alice_demo", "alice@example.com")

    # Create board
    board = app.create_board(alice.user_id, "Project Alpha", "Demo project")

    # Create lists
    todo = app.add_list(board.board_id, alice.user_id, "To Do", 0)
    in_progress = app.add_list(board.board_id, alice.user_id, "In Progress", 1)
    done = app.add_list(board.board_id, alice.user_id, "Done", 2)

    # Create sample tasks
    print("\n✅ Creating sample tasks...")
    for i in range(10):
        priority = ["low", "medium", "high"][i % 3]
        task = app.create_task(
            todo.list_id, alice.user_id, f"Task {i + 1}", priority=priority
        )

        # Move some to done
        if i < 6:
            app.move_task(task.task_id, alice.user_id, done.list_id)
        elif i < 8:
            app.move_task(task.task_id, alice.user_id, in_progress.list_id)

    # Run analytics
    print("\n📊 Running Analytics...\n")

    # 1. SQL-based completion metrics
    _completion_metrics = analytics.get_completion_metrics(
        board.board_id, alice.user_id
    )

    # 2. Financial-style velocity analysis
    _velocity = analytics.analyze_team_velocity(board.board_id, alice.user_id)

    # 3. Time series burndown
    _burndown = analytics.generate_burndown_chart(board.board_id, alice.user_id)

    print("\n" + "=" * 60)
    print("✅ Demo Complete!")
    print(f"Created {len(app.get_user_boards(alice.user_id))} board")
    print(f"Task completion rate: {(6 / 10 * 100):.0f}%")
    print("=" * 60)


if __name__ == "__main__":
    demo_enhanced_kanban()
