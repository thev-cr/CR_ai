# myapp/views.py
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
from joblib import load
from dotenv import load_dotenv
from myapp.database_utils import connect
import json
from bson import ObjectId

pipeline = load('knn_regressor_model.joblib')

def convert_objectid_to_string(data):
    if isinstance(data, dict):
        return {k: convert_objectid_to_string(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_objectid_to_string(v) for v in data]
    elif isinstance(data, ObjectId):
        return str(data)
    else:
        return data
    

# Function to predict university rating
def predict_uni_rating(ug_gpa, gre):
    input_data = pd.DataFrame({'ug_gpa': [ug_gpa], 'gre': [gre], 'status': 'Accepted'})  # status is dummy here
    predicted_rating = pipeline.predict(input_data)[0]
    return predicted_rating



def home_view(request):
    return HttpResponse("Welcome to AI Predictions for Campus Root EduTech Pvt. Ltd.")


def categorize_university(uni_rating, predicted_rating):
    if predicted_rating + 0.65 < uni_rating <= predicted_rating + 1:
        return 'Ambitious'
    elif predicted_rating + 0.25 <= uni_rating <= predicted_rating + 0.65:
        return 'Moderate'
    elif uni_rating < predicted_rating + 0.1896:
        return 'Safe'
    return 'Outside Range'

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

    predicted_rating = predict_uni_rating(ug_gpa, gre)
    universities, courses = connect(chosen_sub_disciplines, predicted_rating)

    matching_universities = {}
    for uni in universities:
        uni_rating = uni.get('uni_rating')
        if uni_rating is None:
            uni_rating = 6
        if uni_rating is not None:
            category = categorize_university(uni_rating, predicted_rating)
            if category != 'Outside Range':
                matching_universities[str(uni['_id'])] = {'name': uni['name'], 'category': category}

    # Initialize lists for Safe, Moderate, Ambitious, and Remaining courses
    output_courses = []

    for course in courses:
    # Assuming `universities` is a list of dictionaries where each dictionary represents a university
    # and includes the '_id' and 'uni_rating' keys.
        university_id = str(course['university'])
        university = next((uni for uni in universities if str(uni['_id']) == university_id), None)
        if university:
            uni_rating = university['uni_rating']
            category = categorize_university(uni_rating, predicted_rating)
            if category != 'Outside Range':
                output_courses.append ({
                    "Course": course['name'],
                    "University": university['name'],
                    "Category": category,
                    "CID": str(course['_id'])
                })


    
    # Convert output data to JSON
    return JsonResponse(output_courses, safe=False)