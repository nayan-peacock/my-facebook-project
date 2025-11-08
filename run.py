import os
from backend import create_app, socketio
# from pyngrok import ngrok  <-- No longer needed
from dotenv import load_dotenv

load_dotenv()

app = create_app()

if __name__ == '__main__':
    # --- All ngrok lines are removed ---
    
    print(f'\n🚀 FaceConnect Backend is LIVE!')
    print(f' * Running on: http://127.0.0.1:5000')
    print(f' * Real-time messaging enabled')
    print(f' * Stories feature active')
    print(f' * Notifications system running')
    print(f'\nReady to connect the world! \n')
    
    # Run the app
    socketio.run(app, port=5000, debug=True, allow_unsafe_werkzeug=True)

#the below code has ngrok in it
#import os
#from backend import create_app, socketio
#from pyngrok import ngrok
#from dotenv import load_dotenv

# Load variables from .env file (like NGROK_AUTH_TOKEN)
#load_dotenv()

#app = create_app()

#if __name__ == '__main__':
    # Set up ngrok
    # This line correctly reads the token from your .env file
#    ngrok.set_auth_token(os.environ.get("NGROK_AUTH_TOKEN"))
#    public_url = ngrok.connect(5000)
    
#    print(f'\n🚀 FaceConnect Backend is LIVE!')
#    print(f' * Local URL: http://127.0.0.1:5000')
#    print(f' * Public URL: {public_url}')
#    print(f' * Real-time messaging enabled')
#    print(f' * Stories feature active')
#    print(f' * Notifications system running')
#    print(f'\nReady to connect the world! \n')
    
    # Run the app
#    socketio.run(app, port=5000, debug=False, allow_unsafe_werkzeug=True)