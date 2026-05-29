"""
Unit tests for LLMFile and LLMMessage content helpers (zango.ai.providers.base).

Pure dataclass logic — no DB, no mocking required.
"""

import base64

from django.test import SimpleTestCase

from zango.ai.providers.base import LLMFile, LLMMessage

PNG_BYTES = b"\x89PNG\r\n\x1a\n"
PDF_BYTES = b"%PDF-1.4"


class LLMFileConstructorTest(SimpleTestCase):
    """Tests for LLMFile named constructors."""

    def test_from_bytes_stores_all_fields(self):
        f = LLMFile.from_bytes(PNG_BYTES, media_type="image/png", filename="photo.png")
        self.assertEqual(f.data, PNG_BYTES)
        self.assertEqual(f.media_type, "image/png")
        self.assertEqual(f.filename, "photo.png")
        self.assertIsNone(f.url)

    def test_from_bytes_filename_optional(self):
        f = LLMFile.from_bytes(PNG_BYTES, media_type="image/png")
        self.assertIsNone(f.filename)

    def test_from_url_guesses_jpeg_from_extension(self):
        f = LLMFile.from_url("https://example.com/scan.jpg")
        self.assertEqual(f.media_type, "image/jpeg")
        self.assertEqual(f.url, "https://example.com/scan.jpg")
        self.assertIsNone(f.data)

    def test_from_url_guesses_png_from_extension(self):
        f = LLMFile.from_url("https://example.com/image.png")
        self.assertEqual(f.media_type, "image/png")

    def test_from_url_explicit_media_type_wins(self):
        f = LLMFile.from_url("https://example.com/file.bin", media_type="application/pdf")
        self.assertEqual(f.media_type, "application/pdf")

    def test_from_url_unknown_extension_gets_fallback(self):
        f = LLMFile.from_url("https://example.com/file.xyz123")
        self.assertEqual(f.media_type, "application/octet-stream")


class LLMFileAnthropicBlockTest(SimpleTestCase):
    """Tests for LLMFile.to_anthropic_block()."""

    def test_bytes_image_produces_base64_image_block(self):
        f = LLMFile.from_bytes(PNG_BYTES, media_type="image/png")
        block = f.to_anthropic_block()
        self.assertEqual(block["type"], "image")
        self.assertEqual(block["source"]["type"], "base64")
        self.assertEqual(block["source"]["media_type"], "image/png")
        expected_b64 = base64.standard_b64encode(PNG_BYTES).decode("utf-8")
        self.assertEqual(block["source"]["data"], expected_b64)

    def test_bytes_pdf_produces_document_block(self):
        f = LLMFile.from_bytes(PDF_BYTES, media_type="application/pdf")
        block = f.to_anthropic_block()
        self.assertEqual(block["type"], "document")
        self.assertEqual(block["source"]["type"], "base64")

    def test_public_url_image_produces_url_image_block(self):
        f = LLMFile.from_url("https://cdn.example.com/img.png", media_type="image/png")
        block = f.to_anthropic_block()
        self.assertEqual(block["type"], "image")
        self.assertEqual(block["source"]["type"], "url")
        self.assertEqual(block["source"]["url"], "https://cdn.example.com/img.png")

    def test_public_url_pdf_produces_url_document_block(self):
        f = LLMFile.from_url("https://cdn.example.com/doc.pdf", media_type="application/pdf")
        block = f.to_anthropic_block()
        self.assertEqual(block["type"], "document")
        self.assertEqual(block["source"]["type"], "url")

    def test_file_id_url_image_produces_file_image_block(self):
        f = LLMFile(url="file-id://abc123", media_type="image/png")
        block = f.to_anthropic_block()
        self.assertEqual(block["type"], "image")
        self.assertEqual(block["source"]["type"], "file")
        self.assertEqual(block["source"]["file_id"], "abc123")

    def test_file_id_url_document_produces_file_document_block(self):
        f = LLMFile(url="file-id://def456", media_type="application/pdf")
        block = f.to_anthropic_block()
        self.assertEqual(block["type"], "document")
        self.assertEqual(block["source"]["type"], "file")
        self.assertEqual(block["source"]["file_id"], "def456")


class LLMFileOpenAIBlockTest(SimpleTestCase):
    """Tests for LLMFile.to_openai_block()."""

    def test_bytes_produces_data_url_block(self):
        f = LLMFile.from_bytes(PNG_BYTES, media_type="image/png")
        block = f.to_openai_block()
        self.assertEqual(block["type"], "image_url")
        expected_b64 = base64.standard_b64encode(PNG_BYTES).decode("utf-8")
        self.assertEqual(
            block["image_url"]["url"],
            f"data:image/png;base64,{expected_b64}"
        )

    def test_public_url_passed_through(self):
        f = LLMFile.from_url("https://example.com/img.png")
        block = f.to_openai_block()
        self.assertEqual(block["type"], "image_url")
        self.assertEqual(block["image_url"]["url"], "https://example.com/img.png")


class LLMMessageContentBuildersTest(SimpleTestCase):
    """Tests for LLMMessage.build_content_for_anthropic/openai."""

    def test_anthropic_no_files_returns_content_unchanged(self):
        msg = LLMMessage(role="user", content="hello")
        self.assertEqual(msg.build_content_for_anthropic(), "hello")

    def test_anthropic_files_plus_string_content(self):
        f = LLMFile.from_bytes(PNG_BYTES, media_type="image/png")
        msg = LLMMessage(role="user", content="Describe this", files=[f])
        result = msg.build_content_for_anthropic()
        # File block first, then text block
        self.assertIsInstance(result, list)
        self.assertEqual(result[0]["type"], "image")
        self.assertEqual(result[1], {"type": "text", "text": "Describe this"})

    def test_anthropic_files_plus_list_content(self):
        f = LLMFile.from_bytes(PNG_BYTES, media_type="image/png")
        existing = [{"type": "text", "text": "Existing block"}]
        msg = LLMMessage(role="user", content=existing, files=[f])
        result = msg.build_content_for_anthropic()
        self.assertEqual(result[0]["type"], "image")
        self.assertEqual(result[1], {"type": "text", "text": "Existing block"})

    def test_openai_no_files_returns_content_unchanged(self):
        msg = LLMMessage(role="user", content="hello")
        self.assertEqual(msg.build_content_for_openai(), "hello")

    def test_openai_files_plus_string_content(self):
        f = LLMFile.from_bytes(PNG_BYTES, media_type="image/png")
        msg = LLMMessage(role="user", content="Describe this", files=[f])
        result = msg.build_content_for_openai()
        self.assertIsInstance(result, list)
        self.assertEqual(result[0]["type"], "image_url")
        self.assertEqual(result[1], {"type": "text", "text": "Describe this"})
