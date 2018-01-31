TRUNCATE TABLE mails_userprofile;

DROP TABLE
  auth_group,
  auth_group_permissions,
  auth_permission,
  auth_user_groups,
  auth_user,
  auth_user_user_permissions,
  django_admin_log,
  django_content_type,
  django_session
CASCADE;
