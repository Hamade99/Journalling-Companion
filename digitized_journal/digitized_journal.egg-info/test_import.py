# test_import.py
try:
    import digitized_journal
    print("Package imported successfully!")
except ImportError as e:
    print(f"Import error: {e}")