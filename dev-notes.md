# DEVELOPMENT NOTES

Uses [pdm](https://pdm.fming.dev/latest/) for package management 

### Make current shell include the nvcl_kit packages

```
eval $(pdm venv activate)
```

### Release the nvcl_kit packages

```
deactivate
```

### Writes to the lock file after you have altered ‘pyproject.toml’

```
pdm lock
```

### Installs packages

```
pdm install
```


### To test, run this in the root repository dir:

```
tox
``` 

# RELEASE PROCEDURE

### Create a new 'X.Y.Z' version of nvcl_kit in pypi package [repository](https://pypi.org/project/nvcl-kit/)

1. Increment version in "pyproject.toml"
2. Commit to git repo
```
git add pyproject.toml
git commit
```
3. Do this:
```
git tag -a vX.Y.Z -m "Version X.Y.Z"
git push --tags origin master
```
4. The CI/CD system will pick up the tagged version and deploy it to pypi

