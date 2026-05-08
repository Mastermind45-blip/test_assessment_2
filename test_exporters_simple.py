#!/usr/bin/env python3
"""Simple test script to verify exporter implementations."""
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_exporter_imports():
    """Test that all exporters can be imported."""
    try:
        # Test importing the exporters module
        from app.infrastructure.exporters import (
            WeatherExporter, JSONExporter, CSVExporter,
            XMLExporter, PDFExporter, MarkdownExporter,
            ExcelExporter, ExportManager
        )
        print("✓ All exporter classes imported successfully!")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("Testing exporter implementations...")
    test_exporter_imports()
    print("Done!")
