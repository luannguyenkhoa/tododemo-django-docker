
APIs:
api_url = “https://docker-machine-ip:8000/api/v1”
Authentication:
Sign_up: POST api_url/authentication/sign_up/
Request params:
{
  “email”: “abc@gmail.com”,
  “password”: “123456”,
  “retype_password”: “123456”,
  “first_name”: “abc” (this field is an optional),
  “last_name”: “xyz” (this field is an optional),
  “original”: image file
}

Response:
{
   "user": {
   "api_key": "a8517fb2033f689d85390c28757578e65e5530dc",
   "email": "abc1@gmail.com",
   "first_name": "abc",
   "id": 1,
   "image": {
   "id": 1,
   "resource_uri": "/api/v1/userimage/1/",
   "medium": "medium-img-url",
   "original": "original-img-url",
   "small": "small-img-url"
},
"is_new": true,
"last_name": "fdf"
}
}

Sign_in: POST api_url/authentication/sign_in/
Request params:
{
  “email”: “abc@gmail.com”,
  “password”: “123456”
}

Response:
{
   "user": {
   "api_key": "a8517fb2033f689d85390c28757578e65e5530dc",
   "email": "abc1@gmail.com",
   "first_name": "abc",
   "id": 1,
   "image": {
   "id": 1,
   "resource_uri": "/api/v1/userimage/1/",
   "medium": "medium-img-url",
   "original": "orignal-img-url",
   "small": "small-img-url"
},
"is_new": true,
"last_name": "fdf"
}

}


Sign_out: POST api_url/authentication/sign_out/
Response: 
{
	“success”: True
}

Create task: POST: api_url/tasks/

Request params:
{
   "title": "The title of task", -> (required)
   “description”: “description of task”, -> (optional)
   "select_date": "June 21, 2016", -> (required)
   "select_time": "08:00 AM - 12:00 PM", -> (required)
   "all_day": false, ->(optional)
   "location": "Da Nang", ->(optional)
   "notification": 1, -> (optional)
   "repeat": false -> (optional)
}
Response:
{
   “id”: 12,
   "title": "The title of task",
   “description”: “description of task”,
   "select_date": "June 21, 2016",
   "select_time": "08:00 AM - 12:00 PM",
   "all_day": false,
   "location": "Da Nang",
   "notification": 1,
   "repeat": false
}

Get list tasks: GET api_url/tasks/listing
Request params:
limit=10,
offset=0,
date=June 1, 2016
Notes: All of these fields is optional fields.

Response:
{
  "meta": {
  "limit": 20,
  "next": null,
  "offset": 0,
  "previous": null,
  "total_count": 1
},
"objects": [
{
  "all_day": 0,
  "description": "",
  "id": 7,
  "is_deleted": false,
  "location": "Da Nang",
  "notification": 1,
  "repeat": 0,
  "select_date": "June 8, 2016",
  "select_time": "11:00 AM - 21:00 PM",
  "title": "New Task"
}
],
"page_number": 1
}

Notes: you must always tie a key-value(“Authorization”: api_key) to each of request as a header field of it expect the sign_in request , the api_key value is that you have got from server when logged-in to the system.
