# myapp/views.py
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
from myapp.database_utils import connect
from joblib import load
import json
from bson import ObjectId
import numpy as np

# Load the models
pipeline = load('knn_regressor_model.joblib')
gre_model = load('gre_prediction_model.joblib')

def normalize_rating(predicted_rating, country):
    # US statistics
    mean_us = 6.1570468555849835
    std_us = 0.6285716772531462
    
    # Statistics for other countries
    country_stats = {
        'United Kingdom': {'mean': 6.455753124873077, 'std': 0.3079073392610625},
        'Australia': {'mean': 6.970986792887201, 'std': 0.5776406361220056},
        'Canada': {'mean': 6.61949587107662, 'std': 0.30279993821056767},
        'Ireland': {'mean': 7.03920163628685, 'std': 0.270550308259789},
        'New Zealand': {'mean': 7.368232450927737, 'std': 0.2143131117040565},
    }

    if country in country_stats:
        mean_country = country_stats[country]['mean']
        std_country = country_stats[country]['std']
        
        # Apply the normalization formula
        normalized_rating = (((predicted_rating - mean_us) / std_us) * std_country + mean_country) - 1.55
        return normalized_rating
    else:
        # If the country is not listed, return the predicted_rating as is
        return predicted_rating
    

# Normalize function for English test scores
def normalize_eng_test(ielts_score, toefl_score, duolingo_score):
    max_scores = {'toefl': 120, 'ielts': 9, 'duolingo': 160}
    ielts_normalized = ielts_score / max_scores['ielts'] if ielts_score is not None else 0
    toefl_normalized = toefl_score / max_scores['toefl'] if toefl_score is not None else 0
    duolingo_normalized = duolingo_score / max_scores['duolingo'] if duolingo_score is not None else 0
    return max(ielts_normalized, toefl_normalized, duolingo_normalized)

# Function to predict university rating for US universities
def predict_uni_rating(ug_gpa, gre):
    input_data = pd.DataFrame({'ug_gpa': [ug_gpa], 'gre': [gre], 'status': 'Accepted'})  # status is dummy here
    predicted_rating = pipeline.predict(input_data)[0]
    # print(predicted_rating)
    return predicted_rating

# Function to categorize US universities
def categorize_university(uni_rating, predicted_rating):
    if predicted_rating + 0.65 < uni_rating <= predicted_rating + 1:
        return 'Ambitious'
    elif predicted_rating + 0.25 <= uni_rating <= predicted_rating + 0.65:
        return 'Moderate'
    elif uni_rating < predicted_rating + 0.1896:
        return 'Safe'
    return 'Outside Range'

def categorize_uni_other(uni_rating, predicted_rating):
    if predicted_rating + 1.25 < uni_rating <= predicted_rating + 1.5:
        return 'Ambitious'
    elif predicted_rating + 0.695 <= uni_rating <= predicted_rating + 0.752 :
        return 'Moderate'
    elif uni_rating < predicted_rating + 0.589 :
        return 'Safe'
    return 'Outside Range'

def home_view(request):
    return HttpResponse("Welcome to AI Predictions for Campus Root EduTech Pvt. Ltd.")




@csrf_exempt
def predict(request):
    data = json.loads(request.body)
    ug_gpa = data.get('ug_gpa')
    gre = data.get('gre')
    country_preference = data.get('country')
    chosen_sub_disciplines = data.get('sub_discipline', [])

    if not isinstance(chosen_sub_disciplines, list):
        chosen_sub_disciplines = [chosen_sub_disciplines.strip()]
    else:
        chosen_sub_disciplines = [sub.strip() for sub in chosen_sub_disciplines]

    # Predict GRE if not provided
    if gre is None:
        ielts_score = data.get('ielts_score')
        toefl_score = data.get('toefl_score')
        duolingo_score = data.get('duolingo_score')

        eng_test = normalize_eng_test(ielts_score, toefl_score, duolingo_score)
        gre = gre_model.predict([[ug_gpa, eng_test]])[0]

    predicted_rating = predict_uni_rating(ug_gpa, gre)

    if country_preference != 'United States of America':
        predicted_rating = normalize_rating(predicted_rating, country_preference)

    # Use the updated connect method to get universities and courses filtered by country
    universities, courses = connect(chosen_sub_disciplines, predicted_rating, country_preference)
    print("courses :", courses)
    if not universities:
        print(f"No universities found for the country: {country_preference}")
        return JsonResponse([], safe=False)

    output_courses = []

    for course in courses:
    # Assuming `universities` is a list of dictionaries where each dictionary represents a university
    # and includes the '_id' and 'uni_rating' keys.
        university_id = str(course['university'])
        university = next((uni for uni in universities if str(uni['_id']) == university_id), None)
        if university:
            uni_rating = university['uni_rating']
            if country_preference == "United States of America":
                category = categorize_university(uni_rating, predicted_rating)
            else:
                category = categorize_uni_other(uni_rating, predicted_rating)
            if category != 'Outside Range':
                output_courses.append ({
                    "Course": course['name'],
                    "University": university['name'],
                    "Category": category,
                    "CID": str(course['_id'])
                })


    # Convert output data to JSON
    return JsonResponse(output_courses, safe=False)










# @csrf_exempt
# def predict(request):
#     data = json.loads(request.body)
#     ug_gpa = data.get('ug_gpa')
#     gre = data.get('gre')
#     country_preference = data.get('country')
#     chosen_sub_disciplines = data.get('sub_discipline', [])

#     if not isinstance(chosen_sub_disciplines, list):
#         chosen_sub_disciplines = [chosen_sub_disciplines.strip()]
#     else:
#         chosen_sub_disciplines = [sub.strip() for sub in chosen_sub_disciplines]

#     # Predict GRE if not provided
#     if gre is None:
#         ielts_score = data.get('ielts_score')
#         toefl_score = data.get('toefl_score')
#         duolingo_score = data.get('duolingo_score')

#         eng_test = normalize_eng_test(ielts_score, toefl_score, duolingo_score)
#         gre = gre_model.predict([[ug_gpa, eng_test]])[0]

#     predicted_rating = predict_uni_rating(ug_gpa, gre)

#     if country_preference != 'United States of America':
#         predicted_rating = normalize_rating(predicted_rating, country_preference)

#     universities, courses = connect(chosen_sub_disciplines, predicted_rating)
#     print("unis :",courses)
    
#     # Filter universities by country preference
#     filtered_universities = [uni for uni in universities if uni['location']['country'] == country_preference]
    
#     if not filtered_universities:
#         print(f"No universities found for the country: {country_preference}")
#         return JsonResponse([], safe=False)

#     final_courses_list = []
    
#     # Loop over universities and categorize them
#     for uni in filtered_universities:
#         uni_rating = uni.get('uni_rating', 6)  # Default rating is 6 if not provided
#         if country_preference == 'United States of America':
#             category = categorize_university(uni_rating, predicted_rating)
#         else:
#             category = categorize_uni_other(uni_rating, predicted_rating)

#         if category != 'Outside Range':
#             # Directly add courses from the categorized universities
#             for course in courses:
#                 if str(course['university']) == str(uni['_id']):
#                     final_courses_list.append({
#                         "Course": course['name'],
#                         "University": uni['name'],
#                         "Category": category,
#                         "CID": str(course['_id'])  # Directly converting ObjectId to string
#                     })

#     print(f"Final Course List: {final_courses_list}")

#     # Convert output data to JSON
#     return JsonResponse(final_courses_list, safe=False)





# @csrf_exempt
# def predict(request):
#     data = json.loads(request.body)
#     ug_gpa = data.get('ug_gpa')
#     gre = data.get('gre')
#     country_preference = data.get('country')
#     chosen_sub_disciplines = data.get('sub_discipline', [])

#     if not isinstance(chosen_sub_disciplines, list):
#         chosen_sub_disciplines = [chosen_sub_disciplines.strip()]
#     else:
#         chosen_sub_disciplines = [sub.strip() for sub in chosen_sub_disciplines]

#     # Predict GRE if not provided
#     if gre is None:
#         ielts_score = data.get('ielts_score')
#         toefl_score = data.get('toefl_score')
#         duolingo_score = data.get('duolingo_score')

#         eng_test = normalize_eng_test(ielts_score, toefl_score, duolingo_score)
#         gre = gre_model.predict([[ug_gpa, eng_test]])[0]

#     predicted_rating = predict_uni_rating(ug_gpa, gre)

#     if country_preference != 'United States of America':
#         predicted_rating = normalize_rating(predicted_rating, country_preference)

#     universities, courses = connect(chosen_sub_disciplines, predicted_rating)
    
#     # Filter universities by country preference
#     filtered_universities = [uni for uni in universities if uni['location']['country'] == country_preference]
    
#     if not filtered_universities:
#         print(f"No universities found for the country: {country_preference}")
#         return JsonResponse([], safe=False)

#     matching_universities = {}
#     for uni in universities:
#         uni_rating = uni.get('uni_rating')
#         if uni_rating is None:
#             if country_preference == 'United States of America':
#                 uni_rating = 6
#             else:
#                 uni_rating = 4.5
#         if uni_rating is not None:
#             if country_preference == 'United States of America':
#                 category = categorize_university(uni_rating, predicted_rating)
#             else:
#                 category = categorize_uni_other(uni_rating, predicted_rating)

#             if category != 'Outside Range':
#                 matching_universities[str(uni['_id'])] = {'name': uni['name'], 'category': category}

  


#     # Filter courses based on the filtered universities list
#     for course in courses:
#         university_id = str(course['university'])
#         if university_id in matching_universities:
#             category = matching_universities[university_id]['category']
#             categorized_courses[category.lower()].append({
#                 "Course": course['name'],
#                 "University": matching_universities[university_id]['name'],
#                 "Category": category,
#                 "CID": str(course['_id'])  # Directly converting ObjectId to string
#             })

#     # Filter the top 10 for each category
#     final_courses_list = []
#     for category in ["safe", "oderate", "Ambitious"]:
#         final_courses_list.extend(categorized_courses[category][:10])

#     print(f"Final Course List: {final_courses_list}")

#     # Convert output data to JSON
#     return JsonResponse(categorized_courses, safe=False)







# @csrf_exempt
# def predict(request):
#     data = json.loads(request.body)
#     ug_gpa = data.get('ug_gpa')
#     gre = data.get('gre')
#     country_preference = data.get('country')
#     chosen_sub_disciplines = data.get('sub_discipline', [])

#     if not isinstance(chosen_sub_disciplines, list):
#         chosen_sub_disciplines = [chosen_sub_disciplines.strip()]
#     else:
#         chosen_sub_disciplines = [sub.strip() for sub in chosen_sub_disciplines]

#     # Predict GRE if not provided
#     if gre is None:
#         ielts_score = data.get('ielts_score')
#         toefl_score = data.get('toefl_score')
#         duolingo_score = data.get('duolingo_score')

#         max_scores = {'toefl': 120, 'ielts': 9, 'duolingo': 160}
#         ielts_normalized = ielts_score / max_scores['ielts'] if ielts_score is not None else 0
#         toefl_normalized = toefl_score / max_scores['toefl'] if toefl_score is not None else 0
#         duolingo_normalized = duolingo_score / max_scores['duolingo'] if duolingo_score is not None else 0
#         eng_test = max(ielts_normalized, toefl_normalized, duolingo_normalized)

#         gre = gre_model.predict([[ug_gpa, eng_test]])[0]

#     predicted_rating = predict_uni_rating(ug_gpa, gre)
    
#     if country_preference != 'United States of America':
#         predicted_rating = normalize_rating(predicted_rating, country_preference)

#     universities, courses = connect(chosen_sub_disciplines, predicted_rating)

#     categorized_courses = {
#         "safe": [],
#         "moderate": [],
#         "ambitious": []
#     }

    # for course in courses:
    #     university_id = str(course['university'])
    #     university = next((uni for uni in universities if str(uni['_id']) == university_id), None)
    #     if university:
    #         uni_rating = university['uni_rating']
    #         if country_preference == 'United States of America':
    #             category = categorize_university(uni_rating, predicted_rating)
    #         else:
    #             category = categorize_uni_other(uni_rating, predicted_rating, country_preference)

    #         if category != 'Outside Range':
    #             categorized_courses[category.lower()].append({
    #                 "Course": course['name'],
    #                 "University": university['name'],
    #                 "Category": category,
    #                 "CID": str(course['_id'])
    #             })

#     for course in courses:
#         university_id = str(course['university'])
#         university = next((uni for uni in universities if str(uni['_id']) == university_id and uni['location']['country'] == country_preference), None)
#         if university:
#             uni_rating = university['uni_rating']
#             print(f"University: {university['name']} | Rating: {uni_rating}")

#             if country_preference == 'United States of America':
#                 category = categorize_university(uni_rating, predicted_rating)
#             else:
#                 # Sort universities by their rating if the country is not the US
#                 sorted_universities = sorted(
#                     (uni for uni in universities if uni['location']['country'] == country_preference),
#                     key=lambda x: x['uni_rating'],
#                     reverse=True
#                 )
#                 print("sorted unis = " ,sorted_universities)
#                 # Categorize universities
#                 if university in sorted_universities[:10]:
#                     category = "Ambitious"
#                 elif university in sorted_universities[10:20]:
#                     category = "Moderate"
#                 elif university in sorted_universities[20:30]:
#                     category = "Safe"
#                 else:
#                     category = "Outside Range"

#             print(f"Course: {course['name']} | Category: {category}")

#             if category != 'Outside Range':
#                 categorized_courses[category.lower()].append({
#                     "Course": course['name'],
#                     "University": university['name'],
#                     "Category": category,
#                     "CID": str(course['_id'])
#                 })

#     # Filter the top 10 for each category
#     final_courses_list = []
#     for category in ["safe", "moderate", "ambitious"]:
#         final_courses_list.extend(categorized_courses[category][:10])

#     print(f"Final Course List: {final_courses_list}")

#     # Convert output data to JSON
#     return JsonResponse(final_courses_list, safe=False)