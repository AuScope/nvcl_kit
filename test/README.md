# Testing

Testing is generally done by running 'tox' from the repository's root directory however you can also
set up testing using VS Code's Testing tab by adding the following to your workspace's `.vscode/settings.json`:

```json
{
  "python.testing.unittestArgs": [
    "-v",
    "-s",
    ".",
    "-p",
    "test_*.py"
  ],
  "python.testing.cwd": "./test",
  "python.testing.pytestEnabled": false,
  "python.testing.unittestEnabled": true,
  "python.testing.autoTestDiscoverOnSaveEnabled": true
}
```


