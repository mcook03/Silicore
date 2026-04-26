# Silicore

Silicore now uses a split architecture:

- `app.py` + `engine/`: Flask backend, analysis logic, auth, jobs, and APIs
- `frontend/`: React + TypeScript + CSS application for the product UI
- `engine/frontend_bridge.py`: the integration layer that serves the built frontend from Flask

## UI Direction

Silicore is no longer a template-first HTML UI project.

Going forward:

- build product UI in `frontend/`
- use React/TypeScript for interaction and state
- use CSS/Tailwind styling for visual design and responsiveness
- keep Flask focused on backend behavior, data, auth, and processing

Legacy Jinja templates still exist as fallback infrastructure, but new UI work should happen in the frontend app.

## Repo Layout

```text
Silicore/
├── app.py
├── engine/
├── frontend/
│   ├── src/
│   ├── package.json
│   └── dist/
├── templates/
├── tests/
└── Dockerfile
```

## Local Development

### Backend

```bash
python3 app.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Build The Frontend For Flask

```bash
cd frontend
npm run build
```

The Flask app serves the built frontend output from `frontend/dist/`.

## Docker

The container now installs Node.js, installs frontend dependencies, and builds the frontend during image creation so the React UI is available when Flask boots.

## Working Rule

If a change is visual, interactive, layout-related, or component-driven, implement it in `frontend/` first.
