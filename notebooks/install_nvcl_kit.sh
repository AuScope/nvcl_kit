!python -m venv ~/venvs/myenv && \
source ~/venvs/myenv/bin/activate && \
pip install --upgrade pip nvcl_kit && \
realpath /env/lib/python3.8/site-packages > ~/venvs/myenv/lib/python3.8/site-packages/base_venv.pth && \
python -m ipykernel install --user --name=myenv --display-name "NVCL KIT"

