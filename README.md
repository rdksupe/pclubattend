---


---

<h2 id="attendance-app">Attendance App</h2>
<p>This app helps a user log its attendance daily by using their face as a medium of authentication. It was developed with a backend written in python using Flask and frontend designed using Bootstrap CSS and client side scripting handled using vanilla JS. The app uses MongoDB for its database and for facial recognition uses the python SDK and a standalone dockerized open-source project by <a href="https://github.com/exadel-inc/CompreFace">Compre-Face</a> . In its present state the app has the following features :</p>
<ul>
<li>User Login and Registration with session management handled using Flask-session and encryption for the passwords handled using Bcrypt hashing library</li>
<li>Well defined api routes for a user to verify their face , log their attendance and even view their past attendance.</li>
<li>Well defined api routes for the admin to view everyones attendance.</li>
</ul>
<h2 id="instructions-for-setup">Instructions for Setup</h2>
<p>Install relevant python dependencies :</p>
<pre><code>pip install -r requirements.txt
</code></pre>
<p>Follow instructions <a href="https://github.com/exadel-inc/CompreFace?tab=readme-ov-file#getting-started-with-compreface">here</a> to setup compre_face and get relevant api-keys to run the app .</p>
<p>replace API_KEY: str  =  ‘’ with your recognition keys from CompreFace<br>
in initial_upload.html replace<br>
const  api_key_detect  =  ‘’ ; with detection api keys</p>
<p>const  api_key_recog  =  ’ '; with recognition api key</p>
<p>Follow instructions <a href="https://www.mongodb.com/docs/manual/administration/install-on-linux/">here</a> to setup mongodb</p>
<p>create a new db named user_management with a users collection and attendance collection and import the relevant json from the repo . Finally run the app :</p>
<pre><code>python3 app.py
</code></pre>
<p>Default admin panel password : admin:admin</p>

