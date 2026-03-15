# VideoFlix Code Documentation

Comprehensive docstring documentation for all major functions, classes, and methods in the VideoFlix project. Organized by module.

## videoflix_app/api/views.py

### `VideoListView` (class, inherits `ListAPIView`)
**Purpose**: API view to list all videos, ordered by creation date (newest first).  
**Permissions**: `IsAuthenticated` with `CookieJWTAuthentication`.  
**Attributes**:
- `queryset`: `Video.objects.all().order_by('-created_at')`
- `serializer_class`: `VideoSerializer`  
**Methods**:
- `get(self, request, *args, **kwargs)`: Returns serialized list of videos.

### `VideoHlsStreamManifestView` (class, inherits `APIView`)
**Purpose**: Serves HLS master manifest (`index.m3u8`) for adaptive streaming.  
**Permissions**: `IsAuthenticated` with `CookieJWTAuthentication`.  
**Path param**: `video_id`, `resolution`  
**Methods**:
- `get(self, request, *args, **kwargs)`: 
  - Validates `video_id` and `resolution`.
  - Constructs path: `VIDEO_ROOT / video_id / resolution / index.m3u8`.
  - Security: Path traversal check.
  - Returns `FileResponse` with `application/vnd.apple.mpegurl` content type.

### `VideoHlsSegmentView` (class, inherits `APIView`)
**Docstring**: \"Serve HLS video segments from MEDIA_ROOT/video/<movie_id>/<resolution>/<segment>.ts\"  
**Permissions**: `IsAuthenticated` with `CookieJWTAuthentication`.  
**Path params**: `video_id`, `resolution`, `segment`  
**Methods**:
- `get(self, request, movie_id=None, resolution=None, segment=None, *args, **kwargs)`:
  - Validates params.
  - Constructs path: `VIDEO_ROOT / video_id / resolution / segment`.
  - Security: Path traversal check.
  - Returns `FileResponse` with `video/MP2T` content type.

## videoflix_app/api/utils.py

### `create_video_thumbnail(video_id)`
**Docstring**: \"Generates a visually representative thumbnail using ffmpeg's thumbnail filter. Avoids black frames automatically.\"  
**Purpose**: Creates JPG thumbnail for video using FFmpeg.  
**Args**:
- `video_id` (int): Video primary key.  
**Process**:
- Fetches `Video` instance.
- Runs FFmpeg: `-vf thumbnail,scale=1280:-1 -frames:v 1 -q:v 2`.
- Saves to `MEDIA_ROOT/thumbnail/{video_id}.jpg`.
- Updates `video.thumbnail_url`.
**Error handling**: Logs warnings/errors.

### `convert_video_to_hls(video_id)`
**Purpose**: Converts video to multi-bitrate HLS streams using FFmpeg.  
**Args**:
- `video_id` (int).  
**Renditions**: 480p (854w), 720p (1280w), 1080p (1920w) with varying bitrates.  
**Process**:
- Creates `VIDEO_ROOT / video_id / {resolution}/index.m3u8`.
- Complex FFmpeg filter for scaling + audio mapping.
- Outputs master playlist `index.m3u8` and variant streams.  
**Error handling**: Logs errors.

### `convert_and_save(video_id)`
**Docstring**: \"convert_and_save is a helper function that retrieves the video by its ID, converts it to HLS format using the convert_to_hls function, and updates the conversion status in the database...\"  
**Purpose**: Orchestrates thumbnail + HLS conversion pipeline.  
**Args**:
- `video_id` (int).  
**Process**:
- Calls `create_video_thumbnail()` and `convert_video_to_hls()`.
- Updates `conversion_status` to 'completed' or 'failed'.
- Sets `error_message` on failure.  
**Error handling**: Catches exceptions, logs.

## auth_app/api/views.py

### `RegistrationView` (class, inherits `APIView`)
**Permissions**: `AllowAny`.  
**Methods**:
- `post(self, request)` **Docstring**: \"Handle user registration...\"  
  - Validates `RegistrationSerializer`.
  - Creates inactive user.
  - Generates activation UID/token.
  - Sends activation email.
  - Returns user info + token.

### `ActivateAccountView` (class, inherits `APIView`)
**Permissions**: `AllowAny`.  
**Methods**:
- `get(self, request, uidb64, token)` **Docstring**: \"Handle account activation...\"  
  - Validates UID/token.
  - Activates user (`is_active=True`).

### `CookieTokenObtainPairView` (class, inherits `TokenObtainPairView`)
**Serializer**: `CustomTokenObtainPairSerializer`.  
**Methods**:
- `post(self, request, *args, **kwargs)` **Docstring**: \"Override the post method to set the JWT token in an HttpOnly cookie...\"  
  - Validates credentials.
  - Sets `access_token` and `refresh_token` HttpOnly cookies.

### `CookieTokenRefreshView` (class, inherits `TokenRefreshView`)
**Docstring**: \"View for refreshing the access token using a cookie-based refresh token.\"  
**Methods**:
- `post(self, request, *args, **kwargs)` **Docstring**: \"Handle POST requests for refreshing the access token.\"  
  - Gets `refresh_token` from cookie.
  - Validates and generates new `access_token` cookie.

### `LogoutView` (class, inherits `APIView`)
**Permissions**: `IsAuthenticated`.  
**Docstring**: \"View for logging out a user by clearing authentication cookies.\"  
**Methods**:
- `post(self, request)` **Docstring**: \"Handle POST requests for logging out a user.\"  
  - Blacklists refresh token.
  - Deletes cookies.

### `ResetPasswordView` (class, inherits `APIView`)
**Permissions**: `AllowAny`.  
**Methods**:
- `post(self, request)` **Docstring**: \"Handle password reset requests...\"  
  - Validates email.
  - Generates UID/token, sends email.

### `PasswordResetConfirmView` (class, inherits `APIView`)
**Permissions**: `AllowAny`.  
**Methods**:
- `post(self, request, uidb64, token)` **Docstring**: \"Handle password reset confirmation...\"  
  - Validates UID/token + new password.
  - Sets new password.

## auth_app/api/serializers.py

### `RegistrationSerializer` (inherits `ModelSerializer`)
**Fields**: `email`, `password`, `confirmed_password`.  
**Methods**:
- `validate_confirmed_password(self, value)` **Docstring**: \"Validate that the confirmed password matches...\"
- `validate_email(self, value)` **Docstring**: \"Validate that the email is unique...\"
- `create(self, validated_data)` **Docstring**: \"Create and save a new user...\"

### `CustomTokenObtainPairSerializer` (inherits `TokenObtainPairSerializer`)
**Docstring**: \"Custom Token Obtain Pair Serializer...\"  
**Methods**:
- `__init__(self, *args, **kwargs)` **Docstring**: \"Initializes the serializer...\"
- `validate(self, attrs)` **Docstring**: \"Validates the user's credentials...\"

### `ResetPasswordSerializer` (inherits `Serializer`)
**Docstring**: \"Serializer for handling password reset requests.\"  
**Methods**:
- `validate_email(self, value)` **Docstring**: \"Validate that the email exists...\"

### `ConfirmPasswordResetSerializer` (inherits `Serializer`)
**Docstring**: \"Serializer for confirming password reset.\"  
**Methods**:
- `validate(self, attrs)` **Docstring**: \"Validate that the new password...\"

## auth_app/api/authentication.py

### `CookieJWTAuthentication` (inherits `JWTAuthentication`)
**Docstring**: \"Custom JWT authentication class that retrieves the token from cookies.\"  
**Methods**:
- `authenticate(self, request)`: Gets `access_token` from cookie, validates.

## videoflix_app/api/serializers.py

### `VideoSerializer` (inherits `ModelSerializer`)
**Fields**: `id`, `title`, `description`, `category`, `thumbnail_url`, `created_at`.  
**Methods**:
- `get_thumbnail_url(self, obj)`: Returns thumbnail URL if exists.

## videoflix_app/api/signals.py

### `video_post_save(sender, instance, created, **kwargs)`
**Purpose**: On `Video` post_save (created), sets status 'processing', enqueues `convert_and_save`.

### `auto_delete_video_on_delete(sender, instance, **kwargs)`
**Docstring**: \"Deletes original video and HLS segments when a Video object is deleted.\"  
**Process**: Deletes `video_file`, `MEDIA_ROOT/hls/{id}`.

## auth_app/utils/activate_email.py

### `send_activation_email(request, user, uid, token)`
**Purpose**: Sends HTML activation email with frontend link.  
**Template**: `emails/activate.html`.



