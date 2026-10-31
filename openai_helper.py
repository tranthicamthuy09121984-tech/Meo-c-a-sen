from openai import OpenAI
client = OpenAI()

stream = client.responses.create(
  model="gpt-6-luna",
  service_tier="fast",
  input=[],
  text={
    "format": {
      "type": "json_object"
    },
    "verbosity": "high"
  },
  reasoning={
    "effort": "max",
    "mode": "pro",
    "summary": "auto"
  },
  tools=[
    {
      "type": "programmatic_tool_calling"
    },
    {
      "type": "image_generation",
      "model": "gpt-image-2-2026-04-21",
      "size": "3840x2160",
      "quality": "high",
      "output_format": "png",
      "background": "auto",
      "moderation": "low",
      "partial_images": 3
    },
    {
      "type": "apply_patch",
      "allowed_callers": [
        "programmatic"
      ]
    },
    {
      "type": "shell",
      "environment": {
        "type": "local"
      },
      "allowed_callers": [
        "programmatic"
      ]
    }
  ],
  stream=True,
  store=True,
  include=[
    "reasoning.encrypted_content",
    "web_search_call.action.sources"
  ]
)

for event in stream:
    print(event)
