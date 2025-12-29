#!/usr/bin/env python3
"""
Example: External Agent Running on Local Machine

This example shows how to create and run an agent on your local machine
that connects to a remote gateway using the task queue pull model.

Usage:
    # Run agent (connects to localhost gateway by default)
    python examples/external_agent_example.py

    # Run with remote gateway
    python examples/external_agent_example.py --gateway https://gateway.example.com
"""

import asyncio
import sys
from pathlib import Path

# Add SDK to path
sys.path.insert(0, str(Path(__file__).parent.parent / "packages" / "unibase-aip-sdk"))

from aip_sdk.external_agent_client import ExternalAgentClient


class TranslatorAgent(ExternalAgentClient):
    """
    Example translator agent that runs locally and pulls tasks from gateway.
    """

    async def execute_task(self, payload: dict) -> dict:
        """
        Translate text from one language to another.

        Payload format:
        {
            "text": "Hello",
            "from_lang": "en",
            "to_lang": "es"
        }
        """
        text = payload.get("text", "")
        from_lang = payload.get("from_lang", "en")
        to_lang = payload.get("to_lang", "es")

        # Mock translation (in real implementation, call translation API)
        translations = {
            ("en", "es"): {"hello": "hola", "world": "mundo"},
            ("en", "fr"): {"hello": "bonjour", "world": "monde"},
            ("es", "en"): {"hola": "hello", "mundo": "world"},
        }

        translation_map = translations.get((from_lang, to_lang), {})
        translated = translation_map.get(text.lower(), f"[{to_lang}] {text}")

        # Simulate processing time
        await asyncio.sleep(0.5)

        return {
            "original_text": text,
            "translated_text": translated,
            "from_lang": from_lang,
            "to_lang": to_lang,
            "agent": self.agent_name
        }


async def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="External Agent Example - Translator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default settings (localhost gateway)
  python examples/external_agent_example.py

  # Run with remote gateway
  python examples/external_agent_example.py --gateway https://gateway.example.com

  # Run with custom agent name
  python examples/external_agent_example.py --name my-translator-1

After starting the agent:
  1. Agent registers with gateway automatically
  2. Agent polls for tasks every 5 seconds
  3. Agent sends heartbeat every 30 seconds
  4. When tasks arrive, agent executes and returns results

Test it by calling the platform:
  curl -X POST http://platform:8001/run -d '{"objective": "Translate hello to Spanish"}'
        """
    )

    parser.add_argument(
        "--gateway",
        default="http://localhost:8080",
        help="Gateway URL (default: http://localhost:8080)"
    )
    parser.add_argument(
        "--name",
        default="translator",
        help="Agent name (default: translator)"
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=5.0,
        help="Poll interval in seconds (default: 5.0)"
    )
    parser.add_argument(
        "--heartbeat-interval",
        type=float,
        default=30.0,
        help="Heartbeat interval in seconds (default: 30.0)"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("External Agent Example - Translator")
    print("=" * 60)
    print(f"Agent Name: {args.name}")
    print(f"Gateway URL: {args.gateway}")
    print(f"Poll Interval: {args.poll_interval}s")
    print(f"Heartbeat Interval: {args.heartbeat_interval}s")
    print("=" * 60)
    print()

    # Create translator agent
    agent = TranslatorAgent(
        agent_name=args.name,
        gateway_url=args.gateway,
        poll_interval=args.poll_interval,
        heartbeat_interval=args.heartbeat_interval,
        capabilities=["translate"],
        metadata={
            "supported_languages": ["en", "es", "fr"],
            "version": "1.0.0",
            "location": "local"
        }
    )

    # Run agent
    try:
        await agent.run()
    except KeyboardInterrupt:
        print("\nAgent stopped by user")
    except Exception as e:
        print(f"\nAgent failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
