# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.memory import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from app.a2ui_utils import a2ui_callback
from app.api_tools import get_currency_exchange_rates
from app.firestore_tools import (
    add_destination,
    get_destination_details,
    list_destinations,
)
from app.maps_tools import find_nearby_places, geocode_address
from app.media_tools import (
    generate_destination_image,
    generate_destination_video,
)

PROJECT_ID = "qwiklabs-gcp-01-8d917c684652"
LOCATION = "us-central1"
MEMORY_BANK_ID = "3175371439075229696"


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        query: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


# WRITE: after each turn, send the session to Memory Bank for durable fact extraction
async def generate_memories_callback(callback_context: CallbackContext):
    try:
        await callback_context.add_session_to_memory()
    except ValueError:
        pass  # Memory service not configured or unavailable for this runner
    return None


# Memory Bank Service configuration for future deployment runs
memory_service = VertexAiMemoryBankService(
    project=PROJECT_ID,
    location=LOCATION,
    agent_engine_id=MEMORY_BANK_ID,
)

# Initialize AgentEngineSandboxCodeExecutor from deployment_metadata.json if present
code_executor = None
metadata_path = Path(__file__).parent.parent / "deployment_metadata.json"
if metadata_path.exists():
    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
            remote_agent_id = metadata.get("remote_agent_runtime_id")
            if remote_agent_id:
                code_executor = AgentEngineSandboxCodeExecutor(
                    agent_engine_resource_name=remote_agent_id
                )
    except Exception as e:
        print(f"Warning: Failed to initialize AgentEngineSandboxCodeExecutor: {e}")


# Build A2UI system prompt using A2uiSchemaManager version 0.8 and BasicCatalog
schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are a Travel Concierge Assistant. You help users explore travel destinations, "
        "find activity recommendations, look up daily costs, convert foreign currency exchange rates, "
        "geocode addresses, search for nearby places (e.g. cafes, restaurants, attractions) using Google Maps, "
        "manage destination records stored in your Firestore database, generate scenic destination previews, "
        "execute Python code for complex travel calculations, and remember user preferences and facts across sessions. "
        "CRITICAL MEMORY & ALLERGY DIRECTIVE: Always identify, remember, and track all user allergies "
        "(such as peanuts, tree nuts, shellfish, gluten, dairy, or environmental/medication allergies) "
        "and dietary restrictions across conversations via Memory Bank. Always check preloaded memory for user "
        "allergies and automatically tailor or filter food, restaurant, cafe, and itinerary recommendations to ensure safety."
    ),
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    code_executor=code_executor,
    instruction=instruction,
    tools=[
        get_weather,
        get_current_time,
        list_destinations,
        get_destination_details,
        add_destination,
        generate_destination_image,
        generate_destination_video,
        get_currency_exchange_rates,
        geocode_address,
        find_nearby_places,
        PreloadMemoryTool(),
    ],
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
