import json
from typing import Dict, Any
from app.ai.assistant import generate_gemini_response
from app.planning.planning_models import ProjectPlan, Milestone, PlanTask

def generate_plan(goal_title: str, goal_description: str = None) -> Dict[str, Any]:
    prompt = f"""
You are an expert project planner. Break down the following goal into a highly structured, actionable project plan.
Goal: {goal_title}
Context: {goal_description or 'None'}

Return a JSON object matching this exact structure (no markdown wrapper, just JSON):
{{
  "title": "String title for the plan",
  "description": "String overall description",
  "milestones": [
    {{
      "title": "Milestone title",
      "description": "Milestone description",
      "tasks": [
        {{
          "title": "Task title",
          "description": "Task description",
          "priority": "high", // low, medium, high
          "estimated_minutes": 60
        }}
      ]
    }}
  ]
}}
"""
    resp, err = generate_gemini_response(prompt)
    if err or not resp:
        return _fallback_plan(goal_title)

    try:
        if resp.startswith("```json"):
            resp = resp.replace("```json\n", "").replace("```", "")
        data = json.loads(resp)
        return data
    except Exception as e:
        print(f"Error parsing Gemini JSON: {e}")
        return _fallback_plan(goal_title)

def _fallback_plan(goal_title: str) -> Dict[str, Any]:
    return {
        "title": f"Plan for: {goal_title}",
        "description": "Generated fallback plan.",
        "milestones": [
            {
                "title": "Preparation",
                "description": "Initial setup phase",
                "tasks": [
                    {
                        "title": "Gather requirements",
                        "description": "Understand what is needed.",
                        "priority": "high",
                        "estimated_minutes": 30
                    }
                ]
            },
            {
                "title": "Execution",
                "description": "Main phase",
                "tasks": [
                    {
                        "title": "Complete main objective",
                        "description": "Work on the core task.",
                        "priority": "high",
                        "estimated_minutes": 120
                    }
                ]
            }
        ]
    }
