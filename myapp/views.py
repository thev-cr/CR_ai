# myapp/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
from joblib import load
from dotenv import load_dotenv
from myapp.database_utils import connect
import json

pipeline = load('knn_regressor_model.joblib')  # Adjust path as necessary


# Function to predict university rating
def predict_uni_rating(ug_gpa, gre):
    input_data = pd.DataFrame({'ug_gpa': [ug_gpa], 'gre': [gre], 'status': 'Accepted'})  # status is dummy here
    predicted_rating = pipeline.predict(input_data)[0]
    return predicted_rating

@csrf_exempt
def predict(request):
    data = json.loads(request.body)
    ug_gpa = data.get('ug_gpa')
    gre = data.get('gre')
    chosen_sub_disciplines = data.get('sub_discipline', [])

    if not isinstance(chosen_sub_disciplines, list):
        chosen_sub_disciplines = [chosen_sub_disciplines.strip()]
    else:
        chosen_sub_disciplines = [sub.strip() for sub in chosen_sub_disciplines]

    # Predict the university rating
    predicted_rating = predict_uni_rating(ug_gpa, gre)

    # Fetch filtered universities and courses based on the chosen sub-disciplines
    universities, courses = connect(chosen_sub_disciplines, predicted_rating)

    # Function to categorize university
    def categorize_university(uni_rating, predicted_rating):
        if predicted_rating - 1 <= uni_rating < predicted_rating - 0.35:
            return 'Safe'
        elif predicted_rating - 0.35 <= uni_rating <= predicted_rating + 0.25:
            return 'Moderate'
        elif predicted_rating + 0.25 < uni_rating <= predicted_rating + 1:
            return 'Ambitious'
        return 'Outside Range'

    matching_universities = {}
    for uni in universities:
        uni_rating = uni.get('uni_rating')
        if uni_rating is None:
            uni_rating = 6
        if uni_rating is not None:
            category = categorize_university(uni_rating, predicted_rating)
            if category != 'Outside Range':
                matching_universities[str(uni['_id'])] = {'name': uni['name'], 'category': category}

    matching_courses_by_sub_discipline = {sub: [] for sub in chosen_sub_disciplines}


    for course in courses:
        try:
            if str(course['university']) in matching_universities and course['subDiscipline'].strip() in chosen_sub_disciplines:
                for sub_discipline in chosen_sub_disciplines:
                    if course['subDiscipline'].strip() == sub_discipline:
                        matching_courses_by_sub_discipline[sub_discipline].append({
                            "Course": course['name'],
                            "University": matching_universities[str(course['university'])]['name'],
                            "Category": matching_universities[str(course['university'])]['category'],
                            "CID": str(course['_id'])
                        })
        except KeyError:
            print(f"Skipping course with ID {str(course['_id'])} due to missing university data.")
            continue

    # Convert output data to JSON
    return JsonResponse(matching_courses_by_sub_discipline)
