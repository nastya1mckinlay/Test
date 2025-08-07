import pandas as pd
import numpy as np
import datetime
import pickle
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.model_selection import train_test_split

# Generate synthetic dataset with 50 entries
np.random.seed(42)

food_tags = ['Healthy', 'Sugary', 'Junk', 'Protein', 'Carbs']
activities = ['Exercise', 'Socializing', 'Gaming', 'Studying', 'Outdoors', 'None']

def random_choices(options, max_len=2):
    length = np.random.randint(1, max_len+1)
    return list(np.random.choice(options, size=length, replace=False))

data = []
base_date = datetime.date.today() - datetime.timedelta(days=50)
for i in range(50):
    date = base_date + datetime.timedelta(days=i)
    foods = random_choices(food_tags)
    acts = random_choices(activities)
    # Assign mood and energy roughly based on food and activity quality
    mood = 3 + 0.8 * ('Healthy' in foods) - 0.8 * ('Junk' in foods) + 0.5 * ('Exercise' in acts) - 0.3 * ('Gaming' in acts)
    energy = 3 + 0.7 * ('Protein' in foods) - 0.7 * ('Sugary' in foods) + 0.6 * ('Outdoors' in acts) - 0.2 * ('None' in acts)
    mood = max(1, min(5, round(mood + np.random.randn()*0.5)))
    energy = max(1, min(5, round(energy + np.random.randn()*0.5)))
    data.append({
        'Date': date,
        'Foods': ', '.join(foods),
        'Activities': ', '.join(acts),
        'Mood': mood,
        'Energy': energy
    })

df = pd.DataFrame(data)
df.to_csv('data.csv', index=False)
print("Generated data.csv with 50 entries.")

# Prepare features using MultiLabelBinarizer
mlb_food = MultiLabelBinarizer(classes=food_tags)
mlb_act = MultiLabelBinarizer(classes=activities)

food_lists = [f.split(', ') for f in df['Foods']]
act_lists = [a.split(', ') for a in df['Activities']]

X_food = mlb_food.fit_transform(food_lists)
X_act = mlb_act.fit_transform(act_lists)

import numpy as np
X = np.hstack([X_food, X_act])
y_mood = df['Mood'].values
y_energy = df['Energy'].values

# Train models
X_train, X_test, y_mood_train, y_mood_test = train_test_split(X, y_mood, test_size=0.2, random_state=42)
_, _, y_energy_train, y_energy_test = train_test_split(X, y_energy, test_size=0.2, random_state=42)

mood_model = RandomForestRegressor(n_estimators=50, random_state=42)
mood_model.fit(X_train, y_mood_train)
energy_model = RandomForestRegressor(n_estimators=50, random_state=42)
energy_model.fit(X_train, y_energy_train)

print(f"Mood model R2 score: {mood_model.score(X_test, y_mood_test):.2f}")
print(f"Energy model R2 score: {energy_model.score(X_test, y_energy_test):.2f}")

# Save models and encoders
with open('mood_model.pkl', 'wb') as f:
    pickle.dump(mood_model, f)
with open('energy_model.pkl', 'wb') as f:
    pickle.dump(energy_model, f)
with open('mlb_food.pkl', 'wb') as f:
    pickle.dump(mlb_food, f)
with open('mlb_act.pkl', 'wb') as f:
    pickle.dump(mlb_act, f)

print("Models and encoders saved as .pkl files.")
