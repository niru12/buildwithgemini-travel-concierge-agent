import asyncio
import uuid
from google import genai
from google.genai import types
from google.cloud import storage
from google.adk.tools import ToolContext

BUCKET_NAME = "travel-concierge-media-qwiklabs-gcp-01-8d917c684652"
PROJECT_ID = "qwiklabs-gcp-01-8d917c684652"


async def generate_destination_image(prompt: str, tool_context: ToolContext) -> str:
    """Generates a scenic preview image for a travel destination or landmark using gemini-3.1-flash-lite-image.

    Saves the image as an ADK artifact for the Playground UI and uploads it to public Cloud Storage.

    Args:
        prompt: A description of the destination or landmark image to generate (e.g. 'A scenic view of Eiffel Tower in Paris during sunset').
        tool_context: ADK tool context provided automatically by the runtime.

    Returns:
        A public HTTPS URL string pointing to the generated image in Cloud Storage.
    """
    try:
        genai_client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location="global",
        )
        response = genai_client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=f"Generate a scenic travel photo of: {prompt}",
        )

        image_bytes = None
        mime_type = "image/jpeg"
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "inline_data") and part.inline_data and part.inline_data.data:
                    image_bytes = part.inline_data.data
                    if part.inline_data.mime_type:
                        mime_type = part.inline_data.mime_type
                    break

        if not image_bytes:
            return "Error: Image generation model did not return image data."

        # 1. Save artifact for Playground UI
        file_ext = "png" if "png" in mime_type else "jpg"
        artifact_filename = f"destination_{uuid.uuid4().hex[:8]}.{file_ext}"
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        await tool_context.save_artifact(filename=artifact_filename, artifact=artifact_part)

        # 2. Upload to public Cloud Storage bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        gcs_filename = f"generated/{uuid.uuid4().hex}.{file_ext}"
        blob = bucket.blob(gcs_filename)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        return f"https://storage.googleapis.com/{BUCKET_NAME}/{gcs_filename}"
    except Exception as e:
        return f"Error generating image: {e}"


async def generate_destination_video(prompt: str, tool_context: ToolContext) -> str:
    """Generates a short video preview for a travel destination or landmark using Google's Omni / Veo model in the global region.

    Saves the video as an ADK artifact for the Playground UI and uploads it to public Cloud Storage.

    Args:
        prompt: A description of the destination or landmark video to generate (e.g. 'A scenic aerial video of tropical Hawaiian beaches at sunset').
        tool_context: ADK tool context provided automatically by the runtime.

    Returns:
        A public HTTPS URL string pointing to the generated video in Cloud Storage.
    """
    try:
        genai_client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location="global",
        )
        model_name = "gemini-omni-flash-preview"
        gcs_output_uri = f"gs://{BUCKET_NAME}/videos/"
        try:
            operation = genai_client.models.generate_videos(
                model=model_name,
                source={"prompt": f"A scenic travel video of: {prompt}"},
                config={"output_gcs_uri": gcs_output_uri},
            )
        except Exception:
            model_name = "veo-3.1-generate-001"
            operation = genai_client.models.generate_videos(
                model=model_name,
                source={"prompt": f"A scenic travel video of: {prompt}"},
                config={"output_gcs_uri": gcs_output_uri},
            )

        while not operation.done:
            await asyncio.sleep(5)
            operation = genai_client.operations.get(operation)

        if not operation.response or not operation.response.generated_videos:
            return "Error: Video generation model did not return video results."

        video_gcs_uri = operation.response.generated_videos[0].video.uri
        blob_name = video_gcs_uri.replace(f"gs://{BUCKET_NAME}/", "")

        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(blob_name)
        video_bytes = blob.download_as_bytes()

        # 1. Save artifact for Playground UI
        artifact_filename = f"destination_video_{uuid.uuid4().hex[:8]}.mp4"
        artifact_part = types.Part.from_bytes(data=video_bytes, mime_type="video/mp4")
        await tool_context.save_artifact(filename=artifact_filename, artifact=artifact_part)

        # 2. Return public HTTPS URL
        return f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_name}"
    except Exception as e:
        return f"Error generating video: {e}"

