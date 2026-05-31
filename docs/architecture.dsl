workspace "Astraeus AI" "AI-powered video editing platform with independent FFmpeg-based core and HyperFrames AI layer" {

    !identifiers hierarchical

    model {
        # ============================================================
        # PEOPLE
        # ============================================================
        contentCreator = person "Content Creator" "End user who edits videos and uses AI features to generate overlays, captions, and motion graphics." "User"
        adminUser = person "Administrator" "Manages users, monitors rendering jobs, and oversees platform health." "Admin"

        # ============================================================
        # EXTERNAL SYSTEMS
        # ============================================================
        objectStorage = softwareSystem "DigitalOcean Spaces" "S3-compatible object storage for user media uploads and rendered video outputs." "External"
        claudeApi = softwareSystem "Anthropic Claude API" "LLM used to generate HyperFrames HTML compositions and JSON edits from user prompts." "External,AI"
        hyperframesService = softwareSystem "HyperFrames" "HTML-to-video rendering engine used exclusively for AI-generated overlays and motion graphics." "External,AI"
        whisperApi = softwareSystem "OpenAI Whisper API" "Speech-to-text service used for automatic caption generation." "External,AI"
        elevenLabsApi = softwareSystem "ElevenLabs API" "AI voice synthesis service used for generating voiceovers." "External,AI"

        # ============================================================
        # ASTRAEUS AI - MAIN SOFTWARE SYSTEM
        # ============================================================
        astraeus = softwareSystem "Astraeus AI" "Browser-based AI video editing platform with proprietary JSON composition engine and FFmpeg rendering core." {

            # ============================================================
            # CONTAINERS
            # ============================================================
            webApp = container "Web Application" "Next.js single-page application providing the video editor UI, timeline, preview player, and project management." "Next.js, React, TypeScript, Tailwind CSS" "WebApp"

            apiGateway = container "API Gateway" "FastAPI service exposing REST endpoints for auth, projects, media, rendering jobs, and AI features." "Python, FastAPI, Pydantic v2" "API" {
                authController = component "Auth Controller" "Handles registration, login, and JWT token issuance." "FastAPI Router"
                userController = component "User Controller" "Manages user profile, settings, and subscription state." "FastAPI Router"
                projectController = component "Project Controller" "Creates, retrieves, updates, and deletes video projects and their JSON compositions." "FastAPI Router"
                mediaController = component "Media Controller" "Handles media upload, listing, and signed-URL generation for storage." "FastAPI Router"
                renderController = component "Render Controller" "Submits, monitors, and cancels FFmpeg rendering jobs." "FastAPI Router"
                aiController = component "AI Controller" "Exposes endpoints for AI prompts: caption generation, overlay generation, voiceover, B-roll." "FastAPI Router"

                authService = component "Auth Service" "JWT issuance, password hashing, and session validation." "Service Layer"
                projectService = component "Project Service" "Business logic for project CRUD and composition JSON validation." "Service Layer"
                mediaService = component "Media Service" "Upload pipeline, mime validation, signed URL generation." "Service Layer"
                renderService = component "Render Service" "Job submission to render queue and status tracking." "Service Layer"
                aiService = component "AI Service" "Dispatches AI tasks to the AI Orchestrator and returns updated composition." "Service Layer"

                exceptionHandler = component "Global Exception Handler" "Centralized error handling and standardized error responses." "Middleware"
                corsMiddleware = component "CORS Middleware" "Cross-origin request handling for the web app." "Middleware"
            }

            compositionEngine = container "Composition Engine" "Core IP. Validates, normalizes, and serializes the proprietary JSON composition format that describes a full video project." "Python Library" "Core" {
                schemaValidator = component "Schema Validator" "Pydantic v2 models that validate composition JSON against the proprietary schema." "Pydantic"
                trackResolver = component "Track Resolver" "Resolves track ordering, layering, and z-index for video, audio, text, image, and AI overlay tracks." "Python"
                timelineNormalizer = component "Timeline Normalizer" "Normalizes clip start/end times, trims, and detects overlap conflicts." "Python"
                compositionSerializer = component "Composition Serializer" "Serializes and deserializes compositions for storage and rendering pipeline input." "Python"
            }

            renderWorker = container "FFmpeg Render Worker" "Background worker that consumes render jobs and executes FFmpeg pipelines to produce MP4 output." "Python, Celery, FFmpeg" "Worker" {
                jobConsumer = component "Job Consumer" "Pulls render jobs from the queue and orchestrates the render lifecycle." "Celery Worker"
                compositionParser = component "Composition Parser" "Parses validated JSON composition into an internal render plan." "Python"
                filterGraphBuilder = component "FFmpeg Filter Graph Builder" "Translates the render plan into an FFmpeg complex filter graph." "Python"
                commandExecutor = component "FFmpeg Command Executor" "Spawns and supervises the FFmpeg subprocess." "subprocess, FFmpeg"
                progressTracker = component "Progress Tracker" "Parses FFmpeg progress output and publishes status updates." "Python"
                outputManager = component "Output Manager" "Uploads finished MP4 to object storage and persists output metadata." "Python"
            }

            aiOrchestrator = container "AI Orchestrator" "Coordinates all AI-driven workflows: prompt-to-overlay, auto-captioning, voiceover, and AI composition generation." "Python, FastAPI" "AI" {
                promptBuilder = component "Prompt Builder" "Constructs structured prompts for Claude based on user input and project context." "Python"
                claudeClient = component "Claude Client" "Calls the Anthropic Claude API to generate HyperFrames HTML or composition JSON." "anthropic-sdk"
                hyperframesClient = component "HyperFrames Client" "Submits AI-generated HTML to the HyperFrames service and retrieves rendered overlay MP4." "HTTP Client"
                whisperClient = component "Whisper Client" "Sends audio to OpenAI Whisper for transcription and caption timing." "openai-sdk"
                elevenLabsClient = component "ElevenLabs Client" "Generates AI voiceover audio from script text." "HTTP Client"
                overlayCompositor = component "AI Overlay Compositor" "Merges AI-generated overlay clips into the main composition JSON." "Python"
            }

            jobQueue = container "Job Queue" "Message broker holding pending render and AI tasks for asynchronous workers." "Redis" "Queue"

            database = container "PostgreSQL Database" "Stores users, projects, compositions, media metadata, render jobs, and audit logs." "PostgreSQL 16" "Database"

            mediaStore = container "Media Cache" "Local working cache for downloaded source media during rendering." "Filesystem" "Storage"
        }

        # ============================================================
        # RELATIONSHIPS - PEOPLE TO SYSTEM
        # ============================================================
        contentCreator -> astraeus "Edits videos, manages projects, triggers AI features, and exports MP4 outputs"
        adminUser -> astraeus "Administers users and monitors rendering health"

        # ============================================================
        # RELATIONSHIPS - WEB APP
        # ============================================================
        contentCreator -> astraeus.webApp "Uses to edit videos" "HTTPS"
        adminUser -> astraeus.webApp "Uses admin dashboard" "HTTPS"
        astraeus.webApp -> astraeus.apiGateway "Makes API calls for auth, projects, media, rendering, and AI features" "JSON over HTTPS"
        astraeus.webApp -> objectStorage "Uploads media directly via signed URLs and downloads rendered output" "HTTPS"

        # ============================================================
        # RELATIONSHIPS - API GATEWAY INTERNAL
        # ============================================================
        astraeus.apiGateway.authController -> astraeus.apiGateway.authService "Delegates auth logic"
        astraeus.apiGateway.userController -> astraeus.apiGateway.authService "Uses for current user context"
        astraeus.apiGateway.projectController -> astraeus.apiGateway.projectService "Delegates project logic"
        astraeus.apiGateway.mediaController -> astraeus.apiGateway.mediaService "Delegates media logic"
        astraeus.apiGateway.renderController -> astraeus.apiGateway.renderService "Delegates render submission"
        astraeus.apiGateway.aiController -> astraeus.apiGateway.aiService "Delegates AI task submission"

        # ============================================================
        # RELATIONSHIPS - API GATEWAY TO OTHER CONTAINERS
        # ============================================================
        astraeus.apiGateway.projectService -> astraeus.compositionEngine "Validates and normalizes composition JSON"
        astraeus.apiGateway.projectService -> astraeus.database "Reads and writes project records" "SQLAlchemy"
        astraeus.apiGateway.authService -> astraeus.database "Reads and writes user credentials" "SQLAlchemy"
        astraeus.apiGateway.mediaService -> astraeus.database "Stores media metadata" "SQLAlchemy"
        astraeus.apiGateway.mediaService -> objectStorage "Generates signed upload and download URLs" "boto3"
        astraeus.apiGateway.renderService -> astraeus.jobQueue "Enqueues render jobs" "Redis Protocol"
        astraeus.apiGateway.renderService -> astraeus.database "Persists job metadata and status" "SQLAlchemy"
        astraeus.apiGateway.aiService -> astraeus.aiOrchestrator "Dispatches AI tasks" "HTTP"
        astraeus.aiOrchestrator -> astraeus.apiGateway "Returns updated composition JSON" "HTTP"

        # ============================================================
        # RELATIONSHIPS - RENDER WORKER INTERNAL
        # ============================================================
        astraeus.renderWorker.jobConsumer -> astraeus.jobQueue "Consumes render jobs" "Redis Protocol"
        astraeus.renderWorker.jobConsumer -> astraeus.renderWorker.compositionParser "Passes job composition"
        astraeus.renderWorker.compositionParser -> astraeus.compositionEngine "Uses for validation and normalization"
        astraeus.renderWorker.compositionParser -> astraeus.renderWorker.filterGraphBuilder "Provides render plan"
        astraeus.renderWorker.filterGraphBuilder -> astraeus.renderWorker.commandExecutor "Provides FFmpeg command"
        astraeus.renderWorker.commandExecutor -> astraeus.renderWorker.progressTracker "Streams stderr for progress parsing"
        astraeus.renderWorker.progressTracker -> astraeus.database "Updates job progress" "SQLAlchemy"
        astraeus.renderWorker.commandExecutor -> astraeus.renderWorker.outputManager "Hands off completed file"
        astraeus.renderWorker.outputManager -> objectStorage "Uploads finished MP4" "boto3"
        astraeus.renderWorker.outputManager -> astraeus.database "Persists output metadata" "SQLAlchemy"
        astraeus.renderWorker.jobConsumer -> astraeus.mediaStore "Caches source media locally during render"
        astraeus.renderWorker.jobConsumer -> objectStorage "Downloads source media for rendering" "boto3"

        # ============================================================
        # RELATIONSHIPS - AI ORCHESTRATOR INTERNAL AND EXTERNAL
        # ============================================================
        astraeus.aiOrchestrator.promptBuilder -> astraeus.aiOrchestrator.claudeClient "Sends structured prompts"
        astraeus.aiOrchestrator.claudeClient -> claudeApi "Generates HyperFrames HTML and composition JSON" "HTTPS"
        astraeus.aiOrchestrator.hyperframesClient -> hyperframesService "Submits HTML and retrieves overlay MP4" "HTTPS"
        astraeus.aiOrchestrator.whisperClient -> whisperApi "Transcribes audio for auto-captions" "HTTPS"
        astraeus.aiOrchestrator.elevenLabsClient -> elevenLabsApi "Synthesizes AI voiceover audio" "HTTPS"
        astraeus.aiOrchestrator.overlayCompositor -> astraeus.compositionEngine "Merges AI overlays into composition"
        astraeus.aiOrchestrator.overlayCompositor -> astraeus.database "Persists AI-generated assets" "SQLAlchemy"
        astraeus.aiOrchestrator.overlayCompositor -> objectStorage "Stores rendered AI overlay clips" "boto3"
    }

    # ============================================================
    # VIEWS
    # ============================================================
    views {
        systemContext astraeus "SystemContext" "Astraeus AI in the context of users and external services." {
            include *
            autolayout lr
        }

        container astraeus "Containers" "Containers within the Astraeus AI platform." {
            include *
            autolayout tb
        }

        component astraeus.apiGateway "APIGatewayComponents" "Components within the API Gateway." {
            include *
            autolayout tb
        }

        component astraeus.renderWorker "RenderWorkerComponents" "Components within the FFmpeg Render Worker." {
            include *
            autolayout tb
        }

        component astraeus.aiOrchestrator "AIOrchestratorComponents" "Components within the AI Orchestrator." {
            include *
            autolayout tb
        }

        component astraeus.compositionEngine "CompositionEngineComponents" "Components within the Composition Engine - the core IP." {
            include *
            autolayout tb
        }

        dynamic astraeus "VideoExportFlow" "Flow of a user exporting a finished video as MP4." {
            contentCreator -> astraeus.webApp "Clicks Export button"
            astraeus.webApp -> astraeus.apiGateway "POST /api/renders with composition JSON"
            astraeus.apiGateway -> astraeus.compositionEngine "Validates composition"
            astraeus.apiGateway -> astraeus.database "Creates render job record"
            astraeus.apiGateway -> astraeus.jobQueue "Enqueues render job"
            astraeus.apiGateway -> astraeus.webApp "Returns job ID and status URL"
            astraeus.renderWorker -> astraeus.jobQueue "Consumes job"
            astraeus.renderWorker -> objectStorage "Downloads source media"
            astraeus.renderWorker -> astraeus.mediaStore "Stages media for FFmpeg processing"
            astraeus.renderWorker -> objectStorage "Uploads finished MP4"
            astraeus.renderWorker -> astraeus.database "Updates job status to completed"
            astraeus.webApp -> astraeus.apiGateway "Polls job status"
            astraeus.webApp -> objectStorage "Downloads finished MP4"
            autolayout lr
        }

        dynamic astraeus "AIOverlayGenerationFlow" "Flow of user generating an AI overlay via Claude and HyperFrames." {
            contentCreator -> astraeus.webApp "Enters prompt: 'Add a lower third for John Doe'"
            astraeus.webApp -> astraeus.apiGateway "POST /api/ai/overlay with prompt and context"
            astraeus.apiGateway -> astraeus.aiOrchestrator "Forwards prompt"
            astraeus.aiOrchestrator -> claudeApi "Sends structured prompt"
            claudeApi -> astraeus.aiOrchestrator "Returns HyperFrames-compatible HTML"
            astraeus.aiOrchestrator -> hyperframesService "Submits HTML for rendering"
            hyperframesService -> astraeus.aiOrchestrator "Returns rendered overlay MP4"
            astraeus.aiOrchestrator -> objectStorage "Stores overlay MP4"
            astraeus.aiOrchestrator -> astraeus.compositionEngine "Merges overlay clip into composition"
            astraeus.aiOrchestrator -> astraeus.apiGateway "Returns updated composition JSON"
            astraeus.apiGateway -> astraeus.webApp "Forwards updated composition to client"
            autolayout lr
        }

        dynamic astraeus "AutoCaptioningFlow" "Flow of generating automatic captions from a video clip audio track." {
            contentCreator -> astraeus.webApp "Clicks Auto-Caption on a video clip"
            astraeus.webApp -> astraeus.apiGateway "POST /api/ai/captions with clip ID"
            astraeus.apiGateway -> astraeus.aiOrchestrator "Dispatches captioning task"
            astraeus.aiOrchestrator -> objectStorage "Fetches audio from clip"
            astraeus.aiOrchestrator -> whisperApi "Sends audio for transcription"
            whisperApi -> astraeus.aiOrchestrator "Returns timed caption segments"
            astraeus.aiOrchestrator -> astraeus.compositionEngine "Inserts captions as text track"
            astraeus.aiOrchestrator -> astraeus.apiGateway "Returns updated composition JSON"
            astraeus.apiGateway -> astraeus.webApp "Forwards updated composition to client"
            autolayout lr
        }

        styles {
            element "Person" {
                background "#08427b"
                color "#ffffff"
                shape person
            }
            element "User" {
                background "#1168bd"
                color "#ffffff"
            }
            element "Admin" {
                background "#444444"
                color "#ffffff"
            }
            element "Software System" {
                background "#1168bd"
                color "#ffffff"
            }
            element "External" {
                background "#999999"
                color "#ffffff"
            }
            element "AI" {
                background "#7a3fbf"
                color "#ffffff"
            }
            element "Container" {
                background "#438dd5"
                color "#ffffff"
            }
            element "WebApp" {
                shape WebBrowser
                background "#3a7ad6"
                color "#ffffff"
            }
            element "API" {
                background "#438dd5"
                color "#ffffff"
            }
            element "Worker" {
                background "#2d8a4e"
                color "#ffffff"
            }
            element "Core" {
                background "#c2410c"
                color "#ffffff"
            }
            element "Queue" {
                shape Pipe
                background "#d97706"
                color "#ffffff"
            }
            element "Database" {
                shape Cylinder
                background "#438dd5"
                color "#ffffff"
            }
            element "Storage" {
                shape Folder
                background "#85bbf0"
                color "#000000"
            }
            element "Component" {
                background "#85bbf0"
                color "#000000"
            }
        }
    }
}