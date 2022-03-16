from django import template
from ..models import Message, MessageContent


register = template.Library()


@register.simple_tag
def get_latest_message(message_id):
    """
    Get the latest message for a given message_id.
    """
    try:
        message = Message.objects.get(pk=message_id)
        latest_message = MessageContent.objects.filter(message=message).latest('created_at')
        return latest_message
    except Message.DoesNotExist:
        return "Message does not exist."
    except MessageContent.DoesNotExist:
        return "No message to show."


@register.simple_tag
def is_latest_read(message_id):
    """
    Check if the latest message for a given message_id is read.
    """
    try:
        message = Message.objects.get(pk=message_id)
        latest_message = MessageContent.objects.filter(message=message).latest('created_at')
        return latest_message.is_read
    except Message.DoesNotExist:
        return "Message does not exist."
    except MessageContent.DoesNotExist:
        return "Message content does not exist."


@register.simple_tag
def get_all_messages(message_id):
    """
    Get all messages for a given message_id.
    """
    try:
        message = Message.objects.get(pk=message_id)
        messages = MessageContent.objects.filter(message=message).order_by('created_at')
        return messages
    except Message.DoesNotExist:
        return "Message does not exist."
    except MessageContent.DoesNotExist:
        return "No message to show."
