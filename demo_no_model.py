import os, random
import numpy as np

class FakeModel:
    def predict(self, img_array):
        val = random.uniform(0.05, 0.95)
        return np.array([[val]])

import app as flask_app
flask_app._model = FakeModel()

if __name__ == "__main__":
    print("=" * 55)
    print("  MODE DEMO — Modèle VGG16 simulé (valeurs aléatoires)")
    print("  Accès : http://127.0.0.1:5000")
    print("  Login : admin / 1234")
    print("=" * 55)
    os.makedirs("static/uploads", exist_ok=True)
    flask_app.app.run(debug=True)
