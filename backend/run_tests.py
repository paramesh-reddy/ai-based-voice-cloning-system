"""
Automated test runner for AI-Based Voice Cloning System.
Can be invoked directly with `python3 run_tests.py` or via `pytest`.
"""

import sys
import traceback
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

def run_all_tests():
    # Try importing pytest first
    try:
        import pytest
        print("Running tests via pytest...")
        exit_code = pytest.main(["-v", "tests"])
        return exit_code
    except ImportError:
        print("pytest not installed; running test suite with native runner...")

    import tests.test_text_validation as t_text
    import tests.test_audio_validation as t_audio
    import tests.test_output_service as t_output
    import tests.test_model_service as t_model
    import tempfile

    modules = [
        ("Text Validation", t_text),
        ("Audio Validation", t_audio),
        ("Output Management", t_output),
        ("Model Service", t_model),
    ]

    passed = 0
    failed = 0
    errors = []

    print("=" * 60)
    print(" AI-Based Voice Cloning System - Test Suite Execution")
    print("=" * 60)

    for name, mod in modules:
        print(f"\n--- Suite: {name} ---")
        for attr_name in dir(mod):
            if attr_name.startswith("test_"):
                fn = getattr(mod, attr_name)
                if callable(fn):
                    test_label = f"{mod.__name__}.{attr_name}"
                    try:
                        # Inspect parameters
                        import inspect
                        sig = inspect.signature(fn)
                        kwargs = {}
                        if "tmp_path" in sig.parameters:
                            with tempfile.TemporaryDirectory() as td:
                                kwargs["tmp_path"] = Path(td)
                                if "valid_wav_file" in sig.parameters:
                                    kwargs["valid_wav_file"] = t_audio.valid_wav_file(Path(td))
                                fn(**kwargs)
                        elif "valid_wav_file" in sig.parameters:
                            with tempfile.TemporaryDirectory() as td:
                                kwargs["valid_wav_file"] = t_audio.valid_wav_file(Path(td))
                                fn(**kwargs)
                        elif "dummy_reference_samples" in sig.parameters:
                            kwargs["dummy_reference_samples"] = t_model.dummy_reference_samples()
                            fn(**kwargs)
                        else:
                            fn()
                        print(f"  [PASS] {attr_name}")
                        passed += 1
                    except Exception as e:
                        print(f"  [FAIL] {attr_name}: {e}")
                        failed += 1
                        errors.append((test_label, traceback.format_exc()))

    print("\n" + "=" * 60)
    print(f" Test Results: {passed} PASSED, {failed} FAILED (Total: {passed + failed})")
    print("=" * 60)

    if errors:
        print("\nFailures:")
        for lbl, tb in errors:
            print(f"\n{lbl}:")
            print(tb)
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(run_all_tests())
