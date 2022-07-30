# Infractions Extension
### Infraction model
name | type | description
--- | --- | ---
id | int | Autoincremented ID
server_id | Snowflake | Server where this infraction took place
timestamp | datetime | When this infraction happened
user_id | Snowflake | User that has this infraction
moderator_id | Snowflake | Moderator that gave this infraction
type | str | Type of this Infraction
reason | str | Reason behind action
duration | timedelta | Duration of action
channel_id | Snowflake | Channel where this happened
message_id | Snowflake | Message that issued a command
expires_at | datetime | When this infraction expires
weight | float | Weight of this infraction

### Commands
```
/infraction     |
    [helper]    - warn [user] [reason] [weight = 1]
                  DMs user with a warning. Saves to database
    [helper]    - timeout [user] [duration] [reason] [weight = 1]
                  Timeouts user. DMs user with a warning. Saves to database
    [helper]    - kick [user] [reason]
                  Kicks user. DMs user with a warning. Saves to database
    [moderator] - ban [user] [reason] [delete_messages = False]
                  Bans user. DMs user with a warning. Saves to database
    [admin]     - unban [user] [reason]
                  Unbans user. Saves to database
    [admin]     - expire [infraction_id]
                  Expires provided infraction
    [global]    - list [user]
                  Shows user infractions
    [admin]     - graph [type] [resample="D"] [locator="Week"] [interval=1] [moderator] [user] [growth=False]
                  Draws graph of infractions by type
    [admin]     - mod_summary [month]
                  Responds with a CSV file containing summary of actions by moderators
```
- When user has at least `moderator` permissions, `/infraction list` will include shortcut buttons: `warn`, `timeout`, `kick` and `ban`
- When user has at least `admin` permissions, `/infraction list` will include select menu allowing to expire infractions
- By default, Infractions expire after 16 weeks (4 months)

```
/report [msg]
DMs currently online moderators with links to report and reported message
```

### Logs
- Report
    - Fires whenever someone uses `/report`
- Infraction
    - Fires whenever someone uses either of: `warn`, `timeout`, `kick`, `ban`, `unban`
    - Also responsible for enabling sending a Direct Message to a user
- Infraction_Event
    - Guild_Ban_Add
        - Fires automatically when someone is banned
    - Guild_Ban_Remove
        - Fires automatically when someone is unbanned
    - Timeout_Event
- Auto_Mod

### Localization keys
- infraction.Warn
- infraction.Mute
- infraction.Ban
- infraction.Unmute
- infraction.Unban
- infraction.Temp_Mute
- infraction.Temp_Ban
- infraction.Kick
- infraction.Timeout
- infraction.for_duration
- infraction.active
- infraction.inactive
- infraction.row
- infraction.title
- infraction.total
- infraction.total_description
- infraction.counter
- infraction.no_infractions
- report.processing
- report.report_author
- report.reference_author
- report.attachments
- report.jump_to_message
- report.result
- report.no_online
- report.report_waiting
- no_reason
- expire_placeholder
- active_infractions
- success_add
- success_expire
- error_target_moderator
- error_dm
- default_reason
- not_found
- already_expired
