# Generated by Django 5.0.4 on 2024-04-25 19:58
import logging

from django.apps.registry import Apps
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

from sentry.new_migrations.migrations import CheckedMigration
from sentry.utils.query import RangeQuerySetWrapperWithProgressBarApprox


def backfill_grouphistory_actor(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    GroupHistory = apps.get_model("sentry", "GroupHistory")
    Actor = apps.get_model("sentry", "Actor")

    for history in RangeQuerySetWrapperWithProgressBarApprox(GroupHistory.objects.all()):
        # Iterate all records as we have lots of records and no good index to filter and order by
        if not history.actor_id:
            continue
        actor = Actor.objects.get(id=history.actor_id)
        changed = False
        if actor.user_id:
            history.user_id = actor.user_id
            changed = True
        elif actor.team_id:
            history.team_id = actor.team_id
            changed = True
        else:
            logging.info("Actor %s is neither a user or team", actor.id)
        if changed:
            history.save(update_fields=["user_id", "team_id"])


class Migration(CheckedMigration):
    # This flag is used to mark that a migration shouldn't be automatically run in production.
    # This should only be used for operations where it's safe to run the migration after your
    # code has deployed. So this should not be used for most operations that alter the schema
    # of a table.
    # Here are some things that make sense to mark as post deployment:
    # - Large data migrations. Typically we want these to be run manually so that they can be
    #   monitored and not block the deploy for a long period of time while they run.
    # - Adding indexes to large tables. Since this can take a long time, we'd generally prefer to
    #   run this outside deployments so that we don't block them. Note that while adding an index
    #   is a schema change, it's completely safe to run the operation after the code has deployed.
    # Once deployed, run these manually via: https://develop.sentry.dev/database-migrations/#migration-deployment

    is_post_deployment = True

    dependencies = [
        ("sentry", "0705_grouphistory_add_userteam"),
    ]

    operations = [
        migrations.RunPython(
            backfill_grouphistory_actor,
            reverse_code=migrations.RunPython.noop,
            hints={"tables": ["sentry_grouphistory", "sentry_actor"]},
        )
    ]
