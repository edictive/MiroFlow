# SPDX-FileCopyrightText: 2025 MiromindAI
#
# SPDX-License-Identifier: Apache-2.0

import base64
import os
import random
import tempfile
import shutil
from anthropic import Anthropic
from openai import OpenAI
from fastmcp import FastMCP
import requests
import asyncio
from typing import List, Optional

import yt_dlp

# Anthropic credentials
ENABLE_CLAUDE_VISION = os.environ.get("ENABLE_CLAUDE_VISION", "false").lower() == "true"
ENABLE_OPENAI_VISION = os.environ.get("ENABLE_OPENAI_VISION", "false").lower() == "true"

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
ANTHROPIC_MODEL_NAME = os.environ.get(
    "ANTHROPIC_MODEL_NAME", "claude-3-7-sonnet-20250219"
)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL_NAME = os.environ.get("OPENAI_MODEL_NAME", "gpt-4o")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL_NAME = os.environ.get("GEMINI_MODEL_NAME", "gemini-2.5-pro")
VISION_PREFERRED_PROVIDER = os.environ.get(
    "VISION_PREFERRED_PROVIDER", ""
).lower()

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.environ.get(
    "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
)
OPENROUTER_GEMINI_MODEL = os.environ.get(
    "OPENROUTER_GEMINI_MODEL", "google/gemini-2.5-pro"
)

# Whisper / transcription fallbacks
OPENAI_WHISPER_API_KEY = os.environ.get("OPENAI_WHISPER_API_KEY")
OPENAI_WHISPER_BASE_URL = os.environ.get(
    "OPENAI_WHISPER_BASE_URL", "https://api.openai.com/v1"
)
OPENAI_WHISPER_MODEL = os.environ.get("OPENAI_WHISPER_MODEL", "whisper-1")
OPENROUTER_TRANSCRIPTION_MODEL = os.environ.get(
    "OPENAI_TRANSCRIPTION_MODEL_NAME", "openai/gpt-4o-mini-transcribe"
)

# Initialize FastMCP server
mcp = FastMCP("vision-mcp-server")


def _get_openrouter_client() -> Optional[OpenAI]:
    """Return an OpenAI client configured for OpenRouter, if credentials exist."""
    if not OPENROUTER_API_KEY:
        return None
    return OpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)


def _get_whisper_client() -> Optional[OpenAI]:
    if OPENAI_WHISPER_API_KEY:
        return OpenAI(
            api_key=OPENAI_WHISPER_API_KEY, base_url=OPENAI_WHISPER_BASE_URL
        )
    if OPENROUTER_API_KEY:
        return OpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)
    return None


async def detect_image_format(file_path: str) -> str:
    try:
        with open(file_path, "rb") as f:
            header = f.read(16)
        if header.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        elif header.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        elif header.startswith(b"GIF87a") or header.startswith(b"GIF89a"):
            return "image/gif"
        elif header.startswith(b"RIFF") and b"WEBP" in header:
            return "image/webp"
        else:
            return await guess_mime_media_type_from_extension(file_path)
    except Exception:
        return await guess_mime_media_type_from_extension(file_path)


async def _load_image_bytes(image_path_or_url: str) -> tuple[bytes, str]:
    """Return raw image bytes and MIME type."""

    if os.path.exists(image_path_or_url):
        with open(image_path_or_url, "rb") as image_file:
            image_data = image_file.read()
        mime_type = await detect_image_format(image_path_or_url)
        return image_data, mime_type

    if "home/user" in image_path_or_url:
        raise ValueError(
            "The visual tools cannot access sandbox files; use a local path provided in the instruction."
        )

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(image_path_or_url, headers=headers)
    response.raise_for_status()
    mime_type = response.headers.get("content-type", "")
    if not mime_type or not mime_type.startswith("image/"):
        mime_type = "image/jpeg"
    return response.content, mime_type


async def _prepare_image_data_url(image_path_or_url: str) -> str:
    data, mime_type = await _load_image_bytes(image_path_or_url)
    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:{mime_type};base64,{b64}"


async def guess_mime_media_type_from_extension(file_path: str) -> str:
    """Guess the MIME type based on the file extension."""
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    if ext in [".jpg", ".jpeg"]:
        return "image/jpeg"
    elif ext == ".png":
        return "image/png"
    elif ext == ".gif":
        return "image/gif"
    elif ext == ".webp":
        return "image/webp"
    else:
        return "image/jpeg"  # Default to JPEG if unknown


async def call_claude_vision(image_path_or_url: str, question: str) -> str:
    """Call Claude vision API."""
    messages_for_llm = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": None,
                },
                {
                    "type": "text",
                    "text": question,
                },
            ],
        }
    ]

    try:
        if os.path.exists(image_path_or_url):  # Check if the file exists locally
            with open(image_path_or_url, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode("utf-8")
                messages_for_llm[0]["content"][0]["source"] = dict(
                    type="base64",
                    media_type=await detect_image_format(image_path_or_url),
                    data=image_data,
                )
        elif "home/user" in image_path_or_url:
            return "The visual_question_answering tool cannot access to sandbox file, please use the local path provided by original instruction"
        else:  # Otherwise, assume it's a URL
            # Convert to https URL for Claude vision API
            url = image_path_or_url
            if url.startswith("http://"):
                url = url.replace("http://", "https://", 1)
            elif not url.startswith("https://"):
                url = "https://" + url

            messages_for_llm[0]["content"][0]["source"] = dict(type="url", url=url)

        max_retries = 4
        for attempt in range(1, max_retries + 1):
            try:
                client = Anthropic(
                    api_key=ANTHROPIC_API_KEY,
                    base_url=ANTHROPIC_BASE_URL,
                )
                response = client.messages.create(
                    model=ANTHROPIC_MODEL_NAME,
                    max_tokens=4096,
                    messages=messages_for_llm,
                )
                result = response.content[0].text

                # Check if response.text is None or empty after stripping
                if result is None or result.strip() == "":
                    raise Exception("Response text is None or empty")

                break  # Success, exit retry loop
            except Exception as e:
                if attempt == max_retries:
                    result = f"[ERROR]: Visual Question Answering (Claude Client) failed after {max_retries} retries: {e}\n"
                    break
                await asyncio.sleep(4**attempt)  # Exponential backoff

        return result

    except Exception as e:
        return f"[ERROR]: Claude Error: {e}"


async def call_openai_vision(image_path_or_url: str, question: str) -> str:
    """Call OpenAI vision API."""
    try:
        if os.path.exists(image_path_or_url):  # Check if the file exists locally
            with open(image_path_or_url, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode("utf-8")
                mime_type = await detect_image_format(image_path_or_url)
                image_content = {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{image_data}"},
                }
        elif "home/user" in image_path_or_url:
            return "The visual_question_answering tool cannot access to sandbox file, please use the local path provided by original instruction"
        else:  # Otherwise, assume it's a URL
            image_content = {
                "type": "image_url",
                "image_url": {"url": image_path_or_url},
            }

        messages_for_llm = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": question,
                    },
                    image_content,
                ],
            }
        ]

        client = OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL,
        )

        response = client.chat.completions.create(
            model=OPENAI_MODEL_NAME,
            max_tokens=4096,
            messages=messages_for_llm,
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"[ERROR]: OpenAI Error: {e}"


async def call_gemini_vision(image_path_or_url: str, question: str) -> str:
    """Call Gemini vision API via OpenRouter."""

    client = _get_openrouter_client()
    if client is None:
        return (
            "[ERROR]: OPENROUTER_API_KEY is not set, Gemini vision via OpenRouter is unavailable."
        )

    try:
        data_url = await _prepare_image_data_url(image_path_or_url)
    except Exception as e:
        return (
            f"[ERROR]: Failed to load image {image_path_or_url}: {e}."
            " Note: Use accessible local paths or HTTP(S) URLs."
        )

    retry_count = 0
    max_retry = 3
    while retry_count <= max_retry:
        try:
            response = client.chat.completions.create(
                model=OPENROUTER_GEMINI_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": question},
                            {
                                "type": "input_image",
                                "image_url": {"url": data_url},
                            },
                        ],
                    }
                ],
                max_tokens=4096,
            )

            result = response.choices[0].message.content
            if not result or not result.strip():
                raise RuntimeError("Empty result from Gemini via OpenRouter")
            return result

        except Exception as e:
            retry_count += 1
            if retry_count > max_retry:
                return f"[ERROR]: Gemini (OpenRouter) error after {max_retry} retries: {e}"
            await asyncio.sleep(min(60, 5 * (2**retry_count)))


def _canonical_provider_name(name: str) -> Optional[str]:
    if not name:
        return None
    normalized = name.strip().lower()
    mapping = {
        "gemini": "gemini",
        "google": "gemini",
        "google-gemini": "gemini",
        "openai": "openai",
        "gpt": "openai",
        "anthropic": "anthropic",
        "claude": "anthropic",
    }
    return mapping.get(normalized)


def _provider_available(provider: str) -> bool:
    if provider == "gemini":
        return bool(OPENROUTER_API_KEY)
    if provider == "openai":
        return bool(OPENAI_API_KEY)
    if provider == "anthropic":
        return bool(ANTHROPIC_API_KEY)
    return False


def _resolve_provider_preferences() -> List[str]:
    preferred: List[str] = []
    if VISION_PREFERRED_PROVIDER:
        preferred = [
            _canonical_provider_name(token)
            for token in VISION_PREFERRED_PROVIDER.split(",")
        ]
        preferred = [token for token in preferred if token]

    default_order = ["gemini", "openai", "anthropic"]
    order: List[str] = []

    for token in preferred + default_order:
        if token and token not in order and _provider_available(token):
            order.append(token)

    return order


async def _invoke_vision_provider(
    provider_order: List[str], image_path_or_url: str, prompt: str
) -> Optional[str]:
    last_error: Optional[str] = None

    for provider in provider_order:
        if provider == "gemini":
            result = await call_gemini_vision(image_path_or_url, prompt)
        elif provider == "openai":
            result = await call_openai_vision(image_path_or_url, prompt)
        elif provider == "anthropic":
            result = await call_claude_vision(image_path_or_url, prompt)
        else:
            continue

        if result and not str(result).startswith("[ERROR]"):
            return result

        last_error = result

    return last_error


async def _download_youtube_audio(url: str) -> tuple[str, str]:
    """Download YouTube audio to a temporary directory using yt_dlp."""

    temp_dir = tempfile.mkdtemp(prefix="vision_yt_")
    output_template = os.path.join(temp_dir, "%(id)s.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
    }

    def _download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)

    try:
        file_path = await asyncio.to_thread(_download)
        return file_path, temp_dir
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise


async def _transcribe_audio(audio_path: str) -> str:
    client = _get_whisper_client()
    if client is None:
        return "[ERROR]: No transcription-capable API key configured for YouTube analysis."

    model = (
        OPENAI_WHISPER_MODEL
        if OPENAI_WHISPER_API_KEY
        else OPENROUTER_TRANSCRIPTION_MODEL
    )

    try:
        with open(audio_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model=model,
                file=audio_file,
            )
    except Exception as e:
        return f"[ERROR]: Failed to transcribe audio: {e}"

    return response.text


async def _answer_question_from_transcript(transcript: str, question: str) -> str:
    prompt = (
        "You are a helpful assistant analyzing a YouTube video transcript.\n"
        "Transcript:\n"
        f"{transcript}\n\n"
        f"Question: {question}\n"
        "Provide a concise, evidence-based answer grounded in the transcript."
    )

    # Prefer OpenRouter Gemini, fall back to provider-specific clients
    openrouter_client = _get_openrouter_client()
    if openrouter_client is not None:
        try:
            response = openrouter_client.chat.completions.create(
                model=OPENROUTER_GEMINI_MODEL,
                messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
                max_tokens=2048,
            )
            content = response.choices[0].message.content
            if content and content.strip():
                return content
        except Exception as e:
            return f"[ERROR]: Gemini (OpenRouter) failed to answer: {e}"

    if OPENAI_API_KEY:
        try:
            client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
            response = client.chat.completions.create(
                model=OPENAI_MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2048,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[ERROR]: OpenAI vision fallback failed: {e}"

    if ANTHROPIC_API_KEY:
        try:
            client = Anthropic(api_key=ANTHROPIC_API_KEY, base_url=ANTHROPIC_BASE_URL)
            response = client.messages.create(
                model=ANTHROPIC_MODEL_NAME,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[-1].text
        except Exception as e:
            return f"[ERROR]: Anthropic fallback failed: {e}"

    return "[ERROR]: No available model to answer the question from transcript."


@mcp.tool()
async def visual_question_answering(image_path_or_url: str, question: str) -> str:
    """This tool is used to ask question about an image or a video and get the answer with Gemini vision language models. It also automatically performs OCR (text extraction) on the image for additional context.

    Args:
        image_path_or_url: The path of the image file locally or its URL. Files from sandbox are not supported.
        question: The question to ask about the image. This tool performs bad on reasoning-required questions.

    Returns:
        The concatenated answers from Gemini vision model, including both VQA responses and OCR results.
    """

    ocr_prompt = """You are a meticulous text extraction specialist. Your task is to carefully scan the entire image and extract ALL visible text with maximum accuracy.

IMPORTANT INSTRUCTIONS:
1. **Scan systematically** - Look at every corner, edge, and area of the image multiple times
2. **Extract ALL text** - Include headers, labels, captions, fine print, watermarks, signs, and any other text elements
3. **Preserve formatting** - Maintain line breaks, spacing, and text hierarchy as they appear
4. **Include numbers and symbols** - Extract all numerical values, symbols, and special characters
5. **Double-check your work** - Review the entire image again to ensure nothing was missed
6. **Describe any unclear, partially visible, or ambiguous text** - If any text is blurry, cut off, partly obscured, or otherwise difficult to read, **describe it as best as possible, even if you are unsure or cannot fully recognize it**.

Remember: Your extraction will be used by someone who cannot see the image themselves. Any possible guess, uncertainty, or ambiguity should be reported in words rather than left out, so that nothing is omitted or lost.

Return only the extracted text content, maintaining the original formatting and structure as much as possible. If there is no text in the image, respond with 'No text found'. If there are areas where text may exist but is unreadable or ambiguous, describe these as well."""

    provider_order = _resolve_provider_preferences()
    if not provider_order:
        return "[ERROR]: No API key is set, visual_question_answering tool is not available."

    ocr_result = await _invoke_vision_provider(
        provider_order, image_path_or_url, ocr_prompt
    )
    if not ocr_result or ocr_result.startswith("[ERROR]"):
        return ocr_result or "[ERROR]: No API key is set, visual_question_answering tool is not available."

    vqa_prompt = f"""You are a highly attentive visual analysis assistant. Your task is to carefully examine the image and provide a thorough, accurate answer to the question.

IMPORTANT INSTRUCTIONS:
1. **Look at the image multiple times** - Take your time to observe all details, objects, people, text, colors, spatial relationships, and any subtle elements
2. **Cross-reference with OCR data** - Carefully compare what you see visually with the extracted text to ensure consistency
3. **Think step-by-step** - Break down your analysis into logical steps before providing your final answer, especially for complex and multi-object recognition questions
4. **Consider multiple perspectives** - Look at the image from different angles and consider various interpretations, especially for multi-object recognition questions
5. **Double-check your observations** - Verify your initial impressions by looking again at specific areas, especially for complex and multi-object recognition questions
6. **Be precise and detailed** - Provide specific details rather than general observations
7. **Report all visible or possible content, even if uncertain or ambiguous** - If you notice anything that is blurry, partly obscured, difficult to recognize, or of uncertain importance, **describe it in words instead of omitting it**. Do not leave out any possible content, even if you are unsure.

Remember: Your analysis will be used by someone who cannot see the image themselves. Any possible guess, uncertainty, or ambiguity should be reported in words rather than left out, so that nothing is omitted or lost.

The OCR result of this image is as follows (may be incomplete or missing some text):
{ocr_result}

Question to answer: {question}

Please provide a comprehensive analysis that demonstrates careful observation and thoughtful reasoning, including any possible, uncertain, or ambiguous elements you notice.
"""
    # Before answering, carefully analyze both the question and the image. Identify and briefly list potential subtle or easily overlooked VQA pitfalls or ambiguities that could arise in interpreting this question or image (e.g., confusing similar objects, missing small details, misreading text, ambiguous context, etc.). For each, suggest a method or strategy to avoid or mitigate these issues. Only after this analysis, proceed to answer the question, providing a thorough and detailed observation and reasoning process.

    vqa_result = await _invoke_vision_provider(
        provider_order, image_path_or_url, vqa_prompt
    )
    if not vqa_result or vqa_result.startswith("[ERROR]"):
        return vqa_result or "[ERROR]: No API key is set, visual_question_answering tool is not available."

    return f"OCR results:\n{ocr_result}\n\nVQA result:\n{vqa_result}"


# The tool visual_audio_youtube_analyzing only support single YouTube URL as input for now, though GEMINI can support multiple URLs up to 10 per request.
@mcp.tool()
async def visual_audio_youtube_analyzing(
    url: str, question: str = "", provide_transcribe: bool = False
) -> str:
    """Analyzes public YouTube video audiovisual content to answer questions or provide transcriptions. This tool processes both audio tracks and visual frames from YouTube videos. This tool could be primarily used when analyzing YouTube video content. Only supports YouTube Video URLs containing youtube.com/watch, youtube.com/shorts, or youtube.com/live for now.

    Args:
        url: The YouTube video URL.
        question: The specific question about the video content. Use timestamp format MM:SS or MM:SS-MM:SS if needed to specify a specific time (e.g., 01:45, 03:20-03:45). Leave empty if only requesting transcription.
        provide_transcribe: When set to true, returns a complete timestamped transcription of both spoken content and visual elements throughout the video.

    Returns:
        The answer to the question or the transcription of the video.
    """
    if GEMINI_API_KEY == "":
        return "[ERROR]: GEMINI_API_KEY is not set, visual_audio_youtube_analyzing tool is not available."

    if (
        "youtube.com/watch" not in url
        and "youtube.com/shorts" not in url
        and "youtube.com/live" not in url
    ):
        return f"[ERROR]: Invalid URL: '{url}'. YouTube Video URL must contain youtube.com/watch, youtube.com/shorts, or youtube.com/live"

    if question == "" and not provide_transcribe:
        return "[ERROR]: You must provide a question to ask about the video content or set provide_transcribe to True."

    try:
        local_audio_path, temp_dir = await _download_youtube_audio(url)
    except Exception as e:
        return f"[ERROR]: Failed to download YouTube audio: {e}"

    try:
        transcript = await _transcribe_audio(local_audio_path)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    if isinstance(transcript, str) and transcript.startswith("[ERROR]"):
        return transcript

    sections = []
    if provide_transcribe:
        sections.append(f"Transcription:\n\n{transcript}\n")

    if question:
        answer = await _answer_question_from_transcript(transcript, question)
        sections.append(
            "Answer:\n\n" + answer
            if answer.strip()
            else "[ERROR]: Failed to generate an answer from the transcript."
        )

    if not sections:
        sections.append("[INFO]: No content generated. Provide a question or set provide_transcribe=true.")

    hint = (
        "\n\nHint: Large videos may trigger rate limits. Consider using `scrape_website` for"
        " supplementary metadata (descriptions, subtitles, etc.)."
    )
    return "\n\n".join(sections) + hint


if __name__ == "__main__":
    mcp.run(transport="stdio")
