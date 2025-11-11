git clone https://github.com/vinicius-moraisdesouza/CEEP.git<br>
py -3.13 -m venv ceep<br>
.\ceep\Scripts\activate ou source ceep/Scripts/activate<br>
pip install -r requirements.txt<br>

git add . <br>
git commit -m "alteração feita"<br>
git push origin main<br>

python manage.py makemigrations<br>
python manage.py migrate<br>