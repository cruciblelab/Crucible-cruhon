# discord.py 2.7.1 — FULL API INVENTORY

Total top-level classes: 253 | Sub-modules: 66 | discord.ext: commands, tasks

Legend: 🔴 async method (needs await) · 🔵 sync method · 🟢 property


======================================================================
## CLIENT / BOT
======================================================================

### discord.Client
  🔴 async (31): application_info, before_identify_hook, change_presence, close, connect, create_application_emoji, create_dm, create_entitlement, delete_invite, fetch_application_emoji, fetch_application_emojis, fetch_channel, fetch_entitlement, fetch_guild, fetch_guild_preview, fetch_invite, fetch_premium_sticker_pack, fetch_premium_sticker_packs, fetch_skus, fetch_soundboard_default_sounds, fetch_stage_instance, fetch_sticker, fetch_template, fetch_user, fetch_webhook, fetch_widget, login, on_error, setup_hook, start, wait_until_ready
  🔵 sync  (24): add_dynamic_items, add_view, clear, create_guild, dispatch, entitlements, event, fetch_guilds, get_all_channels, get_all_members, get_channel, get_emoji, get_guild, get_partial_messageable, get_soundboard_sound, get_stage_instance, get_sticker, get_user, is_closed, is_ready, is_ws_ratelimited, remove_dynamic_items, run, wait_for
  🟢 prop  (18): activity, allowed_mentions, application, application_flags, application_id, cached_messages, emojis, guilds, intents, latency, persistent_views, private_channels, soundboard_sounds, status, stickers, user, users, voice_clients

### discord.AutoShardedClient
  🔴 async (34): application_info, before_identify_hook, change_presence, close, connect, create_application_emoji, create_dm, create_entitlement, delete_invite, fetch_application_emoji, fetch_application_emojis, fetch_channel, fetch_entitlement, fetch_guild, fetch_guild_preview, fetch_invite, fetch_premium_sticker_pack, fetch_premium_sticker_packs, fetch_session_start_limits, fetch_skus, fetch_soundboard_default_sounds, fetch_stage_instance, fetch_sticker, fetch_template, fetch_user, fetch_webhook, fetch_widget, launch_shard, launch_shards, login, on_error, setup_hook, start, wait_until_ready
  🔵 sync  (25): add_dynamic_items, add_view, clear, create_guild, dispatch, entitlements, event, fetch_guilds, get_all_channels, get_all_members, get_channel, get_emoji, get_guild, get_partial_messageable, get_shard, get_soundboard_sound, get_stage_instance, get_sticker, get_user, is_closed, is_ready, is_ws_ratelimited, remove_dynamic_items, run, wait_for
  🟢 prop  (20): activity, allowed_mentions, application, application_flags, application_id, cached_messages, emojis, guilds, intents, latencies, latency, persistent_views, private_channels, shards, soundboard_sounds, status, stickers, user, users, voice_clients

======================================================================
## MESSAGING
======================================================================

### discord.Message
  🔴 async (17): add_files, add_reaction, clear_reaction, clear_reactions, create_thread, delete, edit, end_poll, fetch, fetch_thread, forward, pin, publish, remove_attachments, remove_reaction, reply, unpin
  🔵 sync  (4): is_forwardable, is_system, to_message_reference_dict, to_reference
  🟢 prop  (6): created_at, edited_at, interaction, jump_url, pinned_at, thread

### discord.PartialMessage
  🔴 async (15): add_reaction, clear_reaction, clear_reactions, create_thread, delete, edit, end_poll, fetch, fetch_thread, forward, pin, publish, remove_reaction, reply, unpin
  🔵 sync  (2): to_message_reference_dict, to_reference
  🟢 prop  (4): created_at, jump_url, pinned, thread

### discord.MessageReference
  🔵 sync  (4): from_message, to_dict, to_message_reference_dict, with_state
  🟢 prop  (2): cached_message, jump_url

### discord.Attachment
  🔴 async (3): read, save, to_file
  🔵 sync  (3): is_spoiler, is_voice_message, to_dict
  🟢 prop  (1): flags

### discord.Reaction
  🔴 async (2): clear, remove
  🔵 sync  (2): is_custom_emoji, users

### discord.Embed
  🔵 sync  (14): add_field, clear_fields, copy, from_dict, insert_field_at, remove_author, remove_field, remove_footer, set_author, set_field_at, set_footer, set_image, set_thumbnail, to_dict
  🟢 prop  (11): author, color, colour, fields, flags, footer, image, provider, thumbnail, timestamp, video

### discord.Poll
  🔴 async (1): end
  🔵 sync  (5): add_answer, copy, get_answer, is_finalised, is_finalized
  🟢 prop  (8): answers, created_at, expires_at, message, question, total_votes, victor_answer, victor_answer_id

======================================================================
## KANALLAR
======================================================================

### discord.TextChannel
  🔴 async (15): clone, create_invite, create_thread, create_webhook, delete, delete_messages, edit, fetch_message, follow, invites, move, purge, send, set_permissions, webhooks
  🔵 sync  (10): archived_threads, get_partial_message, get_thread, history, is_news, is_nsfw, overwrites_for, permissions_for, pins, typing
  🟢 prop  (11): category, changed_roles, created_at, jump_url, last_message, members, mention, overwrites, permissions_synced, threads, type

### discord.VoiceChannel
  🔴 async (15): clone, connect, create_invite, create_webhook, delete, delete_messages, edit, fetch_message, invites, move, purge, send, send_sound, set_permissions, webhooks
  🔵 sync  (7): get_partial_message, history, is_nsfw, overwrites_for, permissions_for, pins, typing
  🟢 prop  (12): category, changed_roles, created_at, jump_url, last_message, members, mention, overwrites, permissions_synced, scheduled_events, type, voice_states

### discord.StageChannel
  🔴 async (16): clone, connect, create_instance, create_invite, create_webhook, delete, delete_messages, edit, fetch_instance, fetch_message, invites, move, purge, send, set_permissions, webhooks
  🔵 sync  (7): get_partial_message, history, is_nsfw, overwrites_for, permissions_for, pins, typing
  🟢 prop  (17): category, changed_roles, created_at, instance, jump_url, last_message, listeners, members, mention, moderators, overwrites, permissions_synced, requesting_to_speak, scheduled_events, speakers, type, voice_states

### discord.CategoryChannel
  🔴 async (11): clone, create_forum, create_invite, create_stage_channel, create_text_channel, create_voice_channel, delete, edit, invites, move, set_permissions
  🔵 sync  (3): is_nsfw, overwrites_for, permissions_for
  🟢 prop  (13): category, changed_roles, channels, created_at, forums, jump_url, mention, overwrites, permissions_synced, stage_channels, text_channels, type, voice_channels

### discord.ForumChannel
  🔴 async (11): clone, create_invite, create_tag, create_thread, create_webhook, delete, edit, invites, move, set_permissions, webhooks
  🔵 sync  (7): archived_threads, get_tag, get_thread, is_media, is_nsfw, overwrites_for, permissions_for
  🟢 prop  (12): available_tags, category, changed_roles, created_at, flags, jump_url, members, mention, overwrites, permissions_synced, threads, type

### discord.DMChannel
  🔴 async (2): fetch_message, send
  🔵 sync  (5): get_partial_message, history, permissions_for, pins, typing
  🟢 prop  (5): created_at, guild, jump_url, recipient, type

### discord.GroupChannel
  🔴 async (3): fetch_message, leave, send
  🔵 sync  (4): history, permissions_for, pins, typing
  🟢 prop  (5): created_at, guild, icon, jump_url, type

### discord.Thread
  🔴 async (14): add_tags, add_user, delete, delete_messages, edit, fetch_member, fetch_members, fetch_message, join, leave, purge, remove_tags, remove_user, send
  🔵 sync  (8): get_partial_message, history, is_news, is_nsfw, is_private, permissions_for, pins, typing
  🟢 prop  (13): applied_tags, category, category_id, created_at, flags, jump_url, last_message, members, mention, owner, parent, starter_message, type

### discord.PartialMessageable
  🔴 async (2): fetch_message, send
  🔵 sync  (5): get_partial_message, history, permissions_for, pins, typing
  🟢 prop  (4): created_at, guild, jump_url, mention

======================================================================
## SUNUCU (GUILD)
======================================================================

### discord.Guild
  🔴 async (57): active_threads, ban, bulk_ban, change_voice_state, chunk, create_automod_rule, create_category, create_category_channel, create_custom_emoji, create_forum, create_integration, create_role, create_scheduled_event, create_soundboard_sound, create_stage_channel, create_sticker, create_template, create_text_channel, create_voice_channel, delete_emoji, delete_sticker, edit, edit_onboarding, edit_role_positions, edit_welcome_screen, edit_widget, estimate_pruned_members, fetch_automod_rule, fetch_automod_rules, fetch_ban, fetch_channel, fetch_channels, fetch_emoji, fetch_emojis, fetch_member, fetch_role, fetch_roles, fetch_scheduled_event, fetch_scheduled_events, fetch_soundboard_sound, fetch_soundboard_sounds, fetch_sticker, fetch_stickers, integrations, invites, kick, leave, onboarding, prune_members, query_members, role_member_counts, templates, unban, vanity_invite, webhooks, welcome_screen, widget
  🔵 sync  (19): audit_logs, bans, by_category, delete, dms_paused, fetch_members, get_channel, get_channel_or_thread, get_emoji, get_member, get_member_named, get_role, get_scheduled_event, get_soundboard_sound, get_stage_instance, get_thread, invites_paused, is_dm_spam_detected, is_raid_detected
  🟢 prop  (44): afk_channel, banner, bitrate_limit, categories, channels, chunked, created_at, default_role, discovery_splash, dm_spam_detected_at, dms_paused_until, emoji_limit, filesize_limit, forums, icon, invites_paused_until, large, me, member_count, members, owner, premium_subscriber_role, premium_subscribers, public_updates_channel, raid_detected_at, roles, rules_channel, safety_alerts_channel, scheduled_events, self_role, shard_id, soundboard_sounds, splash, stage_channels, stage_instances, sticker_limit, system_channel, system_channel_flags, text_channels, threads, vanity_url, voice_channels, voice_client, widget_channel

### discord.Role
  🔴 async (3): delete, edit, move
  🔵 sync  (5): is_assignable, is_bot_managed, is_default, is_integration, is_premium_subscriber
  🟢 prop  (13): color, colour, created_at, display_icon, flags, icon, members, mention, permissions, secondary_color, secondary_colour, tertiary_color, tertiary_colour

### discord.Emoji
  🔴 async (5): delete, edit, read, save, to_file
  🔵 sync  (2): is_application_owned, is_usable
  🟢 prop  (4): created_at, guild, roles, url

### discord.PartialEmoji
  🔴 async (3): read, save, to_file
  🔵 sync  (6): from_dict, from_str, is_custom_emoji, is_unicode_emoji, to_dict, with_state
  🟢 prop  (2): created_at, url

### discord.GuildSticker
  🔴 async (5): delete, edit, read, save, to_file
  🟢 prop  (1): created_at

### discord.ScheduledEvent
  🔴 async (5): cancel, delete, edit, end, start
  🔵 sync  (1): users
  🟢 prop  (4): channel, cover_image, guild, url

### discord.Integration
  🔴 async (1): delete

### discord.Widget
  🔴 async (1): fetch_invite
  🟢 prop  (3): created_at, invite_url, json_url

### discord.Template
  🔴 async (3): delete, edit, sync
  🔵 sync  (1): create_guild
  🟢 prop  (1): url

### discord.Onboarding
  🔵 sync  (1): get_prompt

======================================================================
## KULLANICILAR
======================================================================

### discord.User
  🔴 async (3): create_dm, fetch_message, send
  🔵 sync  (4): history, mentioned_in, pins, typing
  🟢 prop  (18): accent_color, accent_colour, avatar, avatar_decoration, avatar_decoration_sku_id, banner, collectibles, color, colour, created_at, default_avatar, display_avatar, display_name, dm_channel, mention, mutual_guilds, primary_guild, public_flags

### discord.Member
  🔴 async (13): add_roles, ban, create_dm, edit, fetch_message, fetch_voice, kick, move_to, remove_roles, request_to_speak, send, timeout, unban
  🔵 sync  (7): get_role, history, is_on_mobile, is_timed_out, mentioned_in, pins, typing
  🟢 prop  (40): accent_color, accent_colour, activity, avatar, avatar_decoration, avatar_decoration_sku_id, banner, bot, collectibles, color, colour, created_at, default_avatar, desktop_status, discriminator, display_avatar, display_banner, display_icon, display_name, dm_channel, flags, global_name, guild_avatar, guild_banner, guild_permissions, id, mention, mobile_status, mutual_guilds, name, primary_guild, public_flags, raw_status, resolved_permissions, roles, status, system, top_role, voice, web_status

### discord.ClientUser
  🔴 async (1): edit
  🔵 sync  (1): mentioned_in
  🟢 prop  (17): accent_color, accent_colour, avatar, avatar_decoration, avatar_decoration_sku_id, banner, collectibles, color, colour, created_at, default_avatar, display_avatar, display_name, mention, mutual_guilds, primary_guild, public_flags

======================================================================
## INTERACTION (slash/button)
======================================================================

### discord.Interaction
  🔴 async (4): delete_original_response, edit_original_response, original_response, translate
  🔵 sync  (3): is_expired, is_guild_integration, is_user_integration
  🟢 prop  (7): app_permissions, channel_id, client, created_at, expires_at, guild, permissions

### discord.InteractionResponse
  🔴 async (7): autocomplete, defer, edit_message, launch_activity, pong, send_message, send_modal
  🔵 sync  (1): is_done
  🟢 prop  (1): type

### discord.InteractionMessage
  🔴 async (17): add_files, add_reaction, clear_reaction, clear_reactions, create_thread, delete, edit, end_poll, fetch, fetch_thread, forward, pin, publish, remove_attachments, remove_reaction, reply, unpin
  🔵 sync  (4): is_forwardable, is_system, to_message_reference_dict, to_reference
  🟢 prop  (6): created_at, edited_at, interaction, jump_url, pinned_at, thread

======================================================================
## PERMISSIONS
======================================================================

### discord.Permissions
  🔵 sync  (19): advanced, all, all_channel, apps, elevated, events, general, handle_overwrite, is_strict_subset, is_strict_superset, is_subset, is_superset, membership, none, stage, stage_moderator, text, update, voice

### discord.PermissionOverwrite
  🔵 sync  (4): from_pair, is_empty, pair, update
  🟢 prop  (59): add_reactions, administrator, attach_files, ban_members, bypass_slowmode, change_nickname, connect, create_events, create_expressions, create_instant_invite, create_polls, create_private_threads, create_public_threads, deafen_members, embed_links, external_emojis, external_stickers, kick_members, manage_channels, manage_emojis, manage_emojis_and_stickers, manage_events, manage_expressions, manage_guild, manage_messages, manage_nicknames, manage_permissions, manage_roles, manage_threads, manage_webhooks, mention_everyone, moderate_members, move_members, mute_members, pin_messages, priority_speaker, read_message_history, read_messages, request_to_speak, send_messages, send_messages_in_threads, send_polls, send_tts_messages, send_voice_messages, set_voice_channel_status, speak, stream, use_application_commands, use_embedded_activities, use_external_apps, use_external_emojis, use_external_sounds, use_external_stickers, use_soundboard, use_voice_activation, view_audit_log, view_channel, view_creator_monetization_analytics, view_guild_insights

======================================================================
## WEBHOOK
======================================================================

### discord.Webhook
  🔴 async (7): delete, delete_message, edit, edit_message, fetch, fetch_message, send
  🔵 sync  (5): from_state, from_url, is_authenticated, is_partial, partial
  🟢 prop  (7): avatar, channel, created_at, default_avatar, display_avatar, guild, url

### discord.WebhookMessage
  🔴 async (17): add_files, add_reaction, clear_reaction, clear_reactions, create_thread, delete, edit, end_poll, fetch, fetch_thread, forward, pin, publish, remove_attachments, remove_reaction, reply, unpin
  🔵 sync  (4): is_forwardable, is_system, to_message_reference_dict, to_reference
  🟢 prop  (6): created_at, edited_at, interaction, jump_url, pinned_at, thread

### discord.SyncWebhook
  🔵 sync  (11): delete, delete_message, edit, edit_message, fetch, fetch_message, from_url, is_authenticated, is_partial, partial, send
  🟢 prop  (7): avatar, channel, created_at, default_avatar, display_avatar, guild, url

======================================================================
## SES
======================================================================

### discord.VoiceClient
  🔴 async (5): connect, disconnect, move_to, on_voice_server_update, on_voice_state_update
  🔵 sync  (12): checked_add, cleanup, create_connection_state, is_connected, is_paused, is_playing, pause, play, resume, send_audio_packet, stop, wait_until_connected
  🟢 prop  (14): average_latency, endpoint, guild, latency, mode, secret_key, session_id, source, ssrc, timeout, token, user, voice_privacy_code, ws

### discord.VoiceProtocol
  🔴 async (4): connect, disconnect, on_voice_server_update, on_voice_state_update
  🔵 sync  (1): cleanup

### discord.AudioSource
  🔵 sync  (3): cleanup, is_opus, read

### discord.FFmpegPCMAudio
  🔵 sync  (3): cleanup, is_opus, read

### discord.PCMVolumeTransformer
  🔵 sync  (3): cleanup, is_opus, read
  🟢 prop  (1): volume

======================================================================
## FILE / MEDIA
======================================================================

### discord.File
  🔵 sync  (3): close, reset, to_dict
  🟢 prop  (2): filename, uri

### discord.Asset
  🔴 async (3): read, save, to_file
  🔵 sync  (5): is_animated, replace, with_format, with_size, with_static_format
  🟢 prop  (2): key, url

### discord.Colour
  🔵 sync  (46): ash_embed, ash_theme, blue, blurple, brand_green, brand_red, dark_blue, dark_embed, dark_gold, dark_gray, dark_green, dark_grey, dark_magenta, dark_orange, dark_purple, dark_red, dark_teal, dark_theme, darker_gray, darker_grey, default, from_hsv, from_rgb, from_str, fuchsia, gold, green, greyple, light_embed, light_gray, light_grey, light_theme, lighter_gray, lighter_grey, magenta, og_blurple, onyx_embed, onyx_theme, orange, pink, purple, random, red, teal, to_rgb, yellow
  🟢 prop  (3): b, g, r

### discord.Color
  🔵 sync  (46): ash_embed, ash_theme, blue, blurple, brand_green, brand_red, dark_blue, dark_embed, dark_gold, dark_gray, dark_green, dark_grey, dark_magenta, dark_orange, dark_purple, dark_red, dark_teal, dark_theme, darker_gray, darker_grey, default, from_hsv, from_rgb, from_str, fuchsia, gold, green, greyple, light_embed, light_gray, light_grey, light_theme, lighter_gray, lighter_grey, magenta, og_blurple, onyx_embed, onyx_theme, orange, pink, purple, random, red, teal, to_rgb, yellow
  🟢 prop  (3): b, g, r

======================================================================
## AUDIT / MODERATION
======================================================================

### discord.AuditLogEntry

### discord.AutoModRule
  🔴 async (2): delete, edit
  🔵 sync  (2): is_exempt, to_dict
  🟢 prop  (1): creator

### discord.AutoModAction
  🔴 async (1): fetch_rule
  🟢 prop  (3): channel, guild, member

### discord.BanEntry# discord.py 2.7.1 — EVENTS, SLASH, UI, EXT, ENUMS, HATALAR

======================================================================
## EVENTLER (on_*) — toplam 79
======================================================================
  on_ready · on_connect · on_disconnect
  on_resumed · on_error · on_shard_ready
  on_message · on_message_edit · on_message_delete
  on_bulk_message_delete · on_message_eta · on_raw_message_edit
  on_raw_message_delete · on_raw_bulk_message_delete · on_reaction_add
  on_reaction_remove · on_reaction_clear · on_reaction_clear_emoji
  on_raw_reaction_add · on_raw_reaction_remove · on_raw_reaction_clear
  on_raw_reaction_clear_emoji · on_typing · on_raw_typing
  on_member_join · on_member_remove · on_member_update
  on_raw_member_remove · on_member_ban · on_member_unban
  on_presence_update · on_user_update · on_guild_join
  on_guild_remove · on_guild_update · on_guild_available
  on_guild_unavailable · on_guild_role_create · on_guild_role_delete
  on_guild_role_update · on_guild_emojis_update · on_guild_stickers_update
  on_audit_log_entry_create · on_guild_channel_create · on_guild_channel_delete
  on_guild_channel_update · on_guild_channel_pins_update · on_guild_integrations_update
  on_webhooks_update · on_thread_create · on_thread_join
  on_thread_update · on_thread_remove · on_thread_delete
  on_thread_member_join · on_thread_member_remove · on_raw_thread_member_remove
  on_voice_state_update · on_stage_instance_create · on_stage_instance_delete
  on_stage_instance_update · on_scheduled_event_create · on_scheduled_event_delete
  on_scheduled_event_update · on_scheduled_event_user_add · on_scheduled_event_user_remove
  on_interaction · on_app_command_completion · on_automod_rule_create
  on_automod_rule_update · on_automod_rule_delete · on_automod_action
  on_poll_vote_add · on_poll_vote_remove · on_raw_poll_vote_add
  on_raw_poll_vote_remove · on_command · on_command_completion
  on_command_error

======================================================================
## SLASH COMMANDS (discord.app_commands)
======================================================================
  Members (69): AllChannels, AppCommand, AppCommandChannel, AppCommandContext, AppCommandError, AppCommandGroup, AppCommandPermissions, AppCommandThread, AppInstallationType, Argument, BotMissingPermissions, CheckFailure, Choice, Command, CommandAlreadyRegistered, CommandInvokeError, CommandLimitReached, CommandNotFound, CommandOnCooldown, CommandSignatureMismatch, CommandSyncFailure, CommandTree, ContextMenu, Cooldown, Group, GuildAppCommandPermissions, MissingAnyRole, MissingApplicationID, MissingPermissions, MissingRole, Namespace, NoPrivateMessage, Parameter, Range, Timestamp, Transform, Transformer, TransformerError, TranslationContext, TranslationContextLocation, TranslationContextTypes, TranslationError, Translator, allowed_contexts, allowed_installs, autocomplete, check, checks, choices, command, commands, context_menu, default_permissions, describe, dm_only, errors, guild_install, guild_only, guilds, installs, locale_str, models, namespace, private_channel_only, rename, transformers, translator, tree, user_install

  app_commands.CommandTree:
    🔴 fetch_command, fetch_commands, interaction_check, on_error, set_translator, sync
    🔵 add_command, clear_commands, command, context_menu, copy_global_to, error, get_command, get_commands, remove_command, walk_commands

  app_commands.Command:
    🔴 get_translated_payload
    🔵 add_check, autocomplete, error, get_parameter, remove_check, to_dict

  app_commands.Group:
    🔴 get_translated_payload, interaction_check, on_error
    🔵 add_command, command, error, get_command, remove_command, to_dict, walk_commands

  app_commands.ContextMenu:
    🔴 get_translated_payload
    🔵 add_check, error, remove_check, to_dict

======================================================================
## UI COMPONENTS (discord.ui)
======================================================================
  Members (44): ActionRow, Button, ChannelSelect, Checkbox, CheckboxGroup, Container, DynamicItem, File, FileUpload, Item, Label, LayoutView, MediaGallery, MentionableSelect, Modal, RadioGroup, RoleSelect, Section, Select, Separator, TextDisplay, TextInput, Thumbnail, UserSelect, View, action_row, button, checkbox, container, dynamic, file, file_upload, item, label, media_gallery, modal, radio, section, select, separator, text_display, text_input, thumbnail, view

  ui.View:
    🔴 interaction_check, on_error, on_timeout, wait
    🔵 add_item, clear_items, find_item, from_message, has_components_v2, is_dispatchable, is_dispatching, is_finished, is_persistent, remove_item, stop, to_components, walk_children

  ui.Button:
    🔴 callback, interaction_check
    🔵 copy, from_component, is_dispatchable, is_persistent, to_component_dict

  ui.Select:
    🔴 callback, interaction_check
    🔵 add_option, append_option, copy, from_component, is_dispatchable, is_persistent, to_component_dict

  ui.Modal:
    🔴 interaction_check, on_error, on_submit, on_timeout, wait
    🔵 add_item, clear_items, find_item, from_message, has_components_v2, is_dispatchable, is_dispatching, is_finished, is_persistent, remove_item, stop, to_components, to_dict, walk_children

  ui.TextInput:
    🔴 callback, interaction_check
    🔵 copy, from_component, is_dispatchable, is_persistent, to_component_dict

======================================================================
## ext.commands (Bot framework)
======================================================================

  commands.Bot:
    🔴 (44) add_cog, application_info, before_identify_hook, can_run, change_presence, close, connect, create_application_emoji, create_dm, create_entitlement, delete_invite, fetch_application_emoji, fetch_application_emojis, fetch_channel, fetch_entitlement, fetch_guild, fetch_guild_preview, fetch_invite, fetch_premium_sticker_pack, fetch_premium_sticker_packs, fetch_skus, fetch_soundboard_default_sounds, fetch_stage_instance, fetch_sticker, fetch_template, fetch_user, fetch_webhook, fetch_widget, get_context, get_prefix, invoke, is_owner, load_extension, login, on_command_error, on_error, on_message, process_commands, reload_extension, remove_cog, setup_hook, start, unload_extension, wait_until_ready
    🔵 (43) add_check, add_command, add_dynamic_items, add_listener, add_view, after_invoke, before_invoke, check, check_once, clear, command, create_guild, dispatch, entitlements, event, fetch_guilds, get_all_channels, get_all_members, get_channel, get_cog, get_command, get_emoji, get_guild, get_partial_messageable, get_soundboard_sound, get_stage_instance, get_sticker, get_user, group, hybrid_command, hybrid_group, is_closed, is_ready, is_ws_ratelimited, listen, recursively_remove_all_commands, remove_check, remove_command, remove_dynamic_items, remove_listener, run, wait_for, walk_commands

  commands.AutoShardedBot:
    🔴 (47) add_cog, application_info, before_identify_hook, can_run, change_presence, close, connect, create_application_emoji, create_dm, create_entitlement, delete_invite, fetch_application_emoji, fetch_application_emojis, fetch_channel, fetch_entitlement, fetch_guild, fetch_guild_preview, fetch_invite, fetch_premium_sticker_pack, fetch_premium_sticker_packs, fetch_session_start_limits, fetch_skus, fetch_soundboard_default_sounds, fetch_stage_instance, fetch_sticker, fetch_template, fetch_user, fetch_webhook, fetch_widget, get_context, get_prefix, invoke, is_owner, launch_shard, launch_shards, load_extension, login, on_command_error, on_error, on_message, process_commands, reload_extension, remove_cog, setup_hook, start, unload_extension, wait_until_ready
    🔵 (44) add_check, add_command, add_dynamic_items, add_listener, add_view, after_invoke, before_invoke, check, check_once, clear, command, create_guild, dispatch, entitlements, event, fetch_guilds, get_all_channels, get_all_members, get_channel, get_cog, get_command, get_emoji, get_guild, get_partial_messageable, get_shard, get_soundboard_sound, get_stage_instance, get_sticker, get_user, group, hybrid_command, hybrid_group, is_closed, is_ready, is_ws_ratelimited, listen, recursively_remove_all_commands, remove_check, remove_command, remove_dynamic_items, remove_listener, run, wait_for, walk_commands

  commands.Cog:
    🔴 (6) cog_after_invoke, cog_app_command_error, cog_before_invoke, cog_command_error, cog_load, cog_unload
    🔵 (12) bot_check, bot_check_once, cog_check, get_app_commands, get_commands, get_listeners, has_app_command_error_handler, has_error_handler, interaction_check, listener, walk_app_commands, walk_commands

  commands.Context:
    🔴 (8) defer, fetch_message, from_interaction, invoke, reinvoke, reply, send, send_help
    🔵 (3) history, pins, typing

  commands.Command:
    🔴 (8) call_after_hooks, call_before_hooks, can_run, dispatch_error, invoke, prepare, reinvoke, transform
    🔵 (11) add_check, after_invoke, before_invoke, copy, error, get_cooldown_retry_after, has_error_handler, is_on_cooldown, remove_check, reset_cooldown, update

  commands.Group:
    🔴 (8) call_after_hooks, call_before_hooks, can_run, dispatch_error, invoke, prepare, reinvoke, transform
    🔵 (18) add_check, add_command, after_invoke, before_invoke, command, copy, error, get_command, get_cooldown_retry_after, group, has_error_handler, is_on_cooldown, recursively_remove_all_commands, remove_check, remove_command, reset_cooldown, update, walk_commands

  commands.GroupCog:
    🔴 (6) cog_after_invoke, cog_app_command_error, cog_before_invoke, cog_command_error, cog_load, cog_unload
    🔵 (12) bot_check, bot_check_once, cog_check, get_app_commands, get_commands, get_listeners, has_app_command_error_handler, has_error_handler, interaction_check, listener, walk_app_commands, walk_commands

  commands decorators/checks/helpers (29): after_invoke, before_invoke, bot_has_any_role, bot_has_guild_permissions, bot_has_permissions, bot_has_role, check, check_any, command, cooldown, dm_only, dynamic_cooldown, flag, group, guild_only, has_any_role, has_guild_permissions, has_permissions, has_role, hybrid_command, hybrid_group, is_nsfw, is_owner, max_concurrency, param, parameter, run_converters, when_mentioned, when_mentioned_or

======================================================================
## ext.tasks
======================================================================
  Any, Callable, Coroutine, ET, ExponentialBackoff, FT, Generic, LF, List, Loop, MISSING, Optional, Sequence, SleepHandle, T, Type, TypeVar, Union, aiohttp, annotations, asyncio, datetime, discord, inspect, is_ambiguous, is_imaginary, logging, loop, overload, resolve_datetime
  tasks.Loop 🔴 
  tasks.Loop 🔵 add_exception_type, after_loop, before_loop, cancel, change_interval, clear_exception_types, error, failed, get_task, is_being_cancelled, is_running, remove_exception_type, restart, start, stop

======================================================================
## ENUM'LAR
======================================================================
  (0): 

======================================================================
## ERROR HIERARCHY
======================================================================
  discord (15): ClientException, ConnectionClosed, DiscordException, DiscordServerError, FFmpegProcessError, Forbidden, GatewayNotFound, HTTPException, InteractionResponded, InvalidData, LoginFailure, MissingApplicationID, NotFound, PrivilegedIntentsRequired, RateLimited
  commands (63): ArgumentParsingError, BadArgument, BadBoolArgument, BadColorArgument, BadColourArgument, BadFlagArgument, BadInviteArgument, BadLiteralArgument, BadTimestampArgument, BadUnionArgument, BotMissingAnyRole, BotMissingPermissions, BotMissingRole, ChannelNotFound, ChannelNotReadable, CheckAnyFailure, CheckFailure, CommandError, CommandInvokeError, CommandNotFound, CommandOnCooldown, CommandRegistrationError, ConversionError, DisabledCommand, EmojiNotFound, ExpectedClosingQuoteError, ExtensionAlreadyLoaded, ExtensionError, ExtensionFailed, ExtensionNotFound, ExtensionNotLoaded, FlagError, GuildNotFound, GuildStickerNotFound, HybridCommandError, InvalidEndOfQuotedStringError, MaxConcurrencyReached, MemberNotFound, MessageNotFound, MissingAnyRole, MissingFlagArgument, MissingPermissions, MissingRequiredArgument, MissingRequiredAttachment, MissingRequiredFlag, MissingRole, NSFWChannelRequired, NoEntryPointError, NoPrivateMessage, NotOwner, ObjectNotFound, PartialEmojiConversionFailure, PrivateMessageOnly, RangeError, RoleNotFound, ScheduledEventNotFound, SoundboardSoundNotFound, ThreadNotFound, TooManyArguments, TooManyFlags, UnexpectedQuoteError, UserInputError, UserNotFound

======================================================================
## INTENTS & FLAGS
======================================================================
  Intents fields (32): DEFAULT_VALUE, VALID_FLAGS, auto_moderation, auto_moderation_configuration, auto_moderation_execution, bans, dm_messages, dm_polls, dm_reactions, dm_typing, emojis, emojis_and_stickers, expressions, guild_messages, guild_polls, guild_reactions, guild_scheduled_events, guild_typing, guilds, integrations, invites, members, message_content, messages, moderation, polls, presences, reactions, typing, value, voice_states, webhooks