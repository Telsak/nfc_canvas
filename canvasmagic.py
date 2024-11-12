import requests

base = 'https://hv.instructure.com/api/v1/'

def get_course_assignments(course_id, token):
    """
    Retrieve a list of assignments for a specific course, excluding any with 'kursvärdering' in the name.

    Args:
        course_id (str): The identifier for the Canvas course.
        token (str): The Canvas API token for authentication.

    Returns:
        list: A list of tuples containing the assignment name, id, and points possible.
    """
    url = f'{base}courses/{course_id}/assignments'
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers).json()
    assignments = []
    for assignment in response:
        if 'kursvärdering' not in assignment['name'].lower():
            assignments.append((assignment['name'], assignment['id'], assignment['points_possible']))
    return assignments

def get_token_status(token: str) -> bool:
    """
    Attempt to fetch a list of the token-holders courses.
    Any 
    
    """
    url = f'{base}/courses'
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"enrollment_type": "teacher"}
    response = requests.get(url, data=payload, headers=headers).json()
    try:
        rlen = len(response)
        return rlen
    except:
        return False

def get_student_info(token, course_id, login_id):
    """
    Retrieve the student ID associated with a specific login ID for a course.

    Args:
        token (str): The Canvas API token for authentication.
        course_id (str): The identifier for the Canvas course.
        login_id (str): The login ID associated with the student.

    Returns:
        tuple (str, str): (The student ID, The student name)
    """
    url = f'{base}courses/{course_id}/search_users'
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"search_term": f"{login_id}"}
    response = requests.get(url, data=payload, headers=headers).json()
    return (response[0]["id"], response[0]["name"])

def get_course_info(token, course_id):
    """
    Retrieve information about a specific Canvas course by course ID.

    Args:
        token (str): The API token for authentication.
        course_id (str or int): The identifier of the course to retrieve information for.

    Returns:
        dict: A dictionary containing the course information in JSON format.
    """
    url = f'{base}courses/{course_id}'
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers).json()
    return response

def set_assignment_completion(token, course_id, assignment, student_id):
    """
    Mark an assignment as completed for a specific student by assigning full points.

    Args:
        token (str): The Canvas API token for authentication.
        course_id (str): The identifier for the Canvas course.
        assignment (tuple): A tuple containing the assignment details (name, id, points possible).
        student_id (str): The student ID.

    Returns:
        dict: The response from the Canvas API after updating the assignment submission.
    """
    assignment_id = assignment[0]
    assignment_points = assignment[1]
    url = f'{base}courses/{course_id}/assignments/{assignment_id}/submissions/{student_id}'
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"submission[posted_grade]": f"{assignment_points}"}
    response = requests.put(url, data=payload, headers=headers)
    return (response.status_code == 200, response.json())
