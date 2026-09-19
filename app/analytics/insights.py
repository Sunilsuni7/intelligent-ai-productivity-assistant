from typing import List
from app.analytics.analytics_models import ProductivityInsight, TaskMetrics, PriorityBreakdown
from app.analytics.metrics import get_task_metrics, get_priority_breakdown, get_overdue_analysis
from app.ai.assistant import generate_gemini_response
import json

def get_rule_based_insights() -> List[ProductivityInsight]:
    insights = []

    # 1. High completion rate
    metrics = get_task_metrics()
    if metrics.completion_rate > 70:
        insights.append(ProductivityInsight(
            type="positive",
            title="High Completion Rate",
            explanation=f"You have a strong completion rate of {metrics.completion_rate:.1f}%. Keep it up!",
            severity="low"
        ))

    # 2. Overdue tasks
    overdue_data = get_overdue_analysis()
    count = overdue_data.get("count", 0)
    if count > 0:
        insights.append(ProductivityInsight(
            type="negative",
            title="Overdue Tasks Need Attention",
            explanation=f"You have {count} overdue tasks.",
            severity="high" if count > 3 else "medium"
        ))

    # 3. Priorities
    pb = get_priority_breakdown()
    if pb.high_total > 0 and (pb.high_completed / pb.high_total) > 0.8:
        insights.append(ProductivityInsight(
            type="positive",
            title="Focusing on Priorities",
            explanation="You are successfully completing most of your high-priority work.",
            severity="low"
        ))

    return insights

def generate_ai_insights(summary_data: dict) -> List[ProductivityInsight]:
    prompt = f"""
Analyze this structured productivity data and provide 3 insightful observations.
Data: {json.dumps(summary_data)}

Return ONLY a JSON list of objects. No markdown. Each object must have:
"type" (positive, negative, or info)
"title" (string)
"explanation" (string)
"severity" (low, medium, high)
"""
    resp, err = generate_gemini_response(prompt)
    if err or not resp:
        return get_rule_based_insights()

    try:
        if resp.startswith("```json"):
            resp = resp.replace("```json\n", "").replace("```", "")
        data = json.loads(resp)
        insights = []
        for item in data:
            insights.append(ProductivityInsight(**item))
        return insights
    except Exception as e:
        print(f"Error parsing Gemini JSON for insights: {e}")
        return get_rule_based_insights()
