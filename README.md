# ScrimSync-Elarcosa-JohnJassim-G1
**ScrimSync** is a centralized esports team management and practice match (scrimmage) scheduling web platform built with Django and Supabase PostgreSQL. It streamlines squad roster coordination, player join requests, and conflict-free scrimmage matchmaking across Competitive Players, Team Managers, Tournament Organizers, and System Administrators.

---

## Core Feature: Team Roster Management & Scrimmage Matchmaking

The Project Development 2 vertical slice delivers end-to-end squad management and scrimmage scheduling inside `apps/scrims/`:

* **Team Roster Management & Squad Join Requests:**
  * **Team Managers** can create, edit, and delete esports squads (`Team`), assign active roster members, and review incoming squad join requests (`TeamJoinRequest`).
  * **Competitive Players** can browse registered squads, submit join requests with an optional role/rank note, and track their active squad memberships (enforcing one active squad per game title).
* **Scrimmage Scheduling & Matchmaking:**
  * **Team Managers** can post open scrimmage challenges (`Scrimmage`) specifying their host squad, future date/time, server region, and match notes.
  * **Validation & Business Rules:** Automatically prevents scheduling scrimmages in the past and enforces a **2-hour conflict detection window** per host squad to prevent double-bookings.
  * **Match Acceptance & Management:** Challenging Team Managers can accept open challenges using an eligible squad registered under the same game title (preventing self-scrimmages), transitioning the match status to **Confirmed / Scheduled**. Hosting managers, Tournament Organizers, and System Admins can edit or cancel/delete scheduled scrimmages.

---

## Tech Stack

* **Backend:** Python 3.12, Django 6.x
* **Database:** PostgreSQL (Supabase) / SQLite local fallback
* **Frontend:** Django Templates, Bootstrap 5
* **Documentation:** `docs/ScrimSync-Elarcosa-JohnJassim-G1-PD2.pdf`

---

## Local Setup & Installation

1. **Clone the repository and switch to `develop`:**
   ```powershell
   git clone [https://github.com/Jazzioh/ScrimSync-Elarcosa-JohnJassim-G1.git](https://github.com/Jazzioh/ScrimSync-Elarcosa-JohnJassim-G1.git)
   cd ScrimSync-Elarcosa-JohnJassim-G1
   git checkout develop