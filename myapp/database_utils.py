import os
import certifi
import pymongo


def connect(chosen_sub_disciplines, rating):
    # MongoDB connection parameters
    mongo_uri = os.environ.get('MONGO_URI')

    try:
        # Connect to MongoDB connection
        client = pymongo.MongoClient(mongo_uri,tlsCAFile=certifi.where())
        db = client.imaginary
        client.admin.command('ping')
        print('Connected to db')
    except pymongo.errors.ConnectionFailure as e:
        print("Error connecting to MongoDB:", e)
        return [], []
    
    collection_name = "universities"
    collection = db[collection_name]

    collection_name_c = "courses"
    collection_c = db[collection_name_c]

    # Query universities based on the rating threshold
    universities = list(collection.find({'uni_rating': {'$gt': rating}}))
    if not universities:
        print("Error: No universities found with a rating greater than the specified threshold.")
        universities = []

    # Extract university IDs
    university_ids = [university['_id'] for university in universities]

    # Initialize an empty list to accumulate courses
    all_courses = []

    # Iterate over each sub-discipline
    for sub_discipline in chosen_sub_disciplines:
        # Query courses based on the current sub-discipline and the extracted university IDs
        courses = list(collection_c.find({
            'subDiscipline': sub_discipline,
            'university': {'$in': university_ids}
        }))

        # If no courses are found for the current sub-discipline, print an error message
        if not courses:
            print(f"Error: No courses found for sub-discipline '{sub_discipline}'.")

        # Accumulate courses from each sub-discipline
        all_courses.extend(courses)

    return universities, all_courses
