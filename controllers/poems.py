# dependencies
import os
import sys
import mongoengine
import readtime
import bson
from flask import request, g


# models
from models.poem import Poem
from models.response import Response
from models.tag import Tag
from models.draft import Draft


# helpers
from helpers.request import read_request_body
from helpers.poems import get_poem_document, update_poem_document, get_tag_document, update_tag_document
from helpers.database import get_from_collection, update_a_document, delete_from_collection


# schema
from schemas.tag import Tag as _Tag
from schemas.poem import Poem as _Poem
from schemas.draft import Draft as _Draft


"""""""""PUBLISHING POEMS"""""""""


def publish_a_poem(did):
    publisher_payload = g.my_request_var["payload"]
    publisher = get_from_collection(
        search_key="email_address", search_value=publisher_payload["email_address"], collection_name="accounts")

    if publisher:
        draft_data = get_from_collection(
            search_key="did", search_value=did, collection_name="drafts")
        if draft_data:
            request_data = read_request_body(request)
            request_tags = request_data.get("tags")

            if not request_tags:
                request_tags = []

            else:
                for index, tag in enumerate(request_tags):
                    if tag != "":
                        request_tags[index] = tag.strip().lower()
                    else:
                        del request_tags[index]

            draft_data["tags"] = request_tags
            if not request_data["is_anonymous"]:
                draft_data["author"] = publisher["_id"]

            poem_data = Poem(draft_data)
            poem = _Poem(**poem_data.__dict__)

            poem.save()

            # delete the draft since it's now published as a poem
            is_deleted = delete_from_collection(
                search_key="did", search_value=did, collection_name="drafts")
            if is_deleted:
                for index, draft in enumerate(publisher["drafts"]):
                    if draft == draft_data["_id"]:
                        del publisher["drafts"][index]
                        # Append it to the list of poems published by the author
                        publisher["poems"].append(poem._id)
                        update_a_document(
                            publisher, collection_name="accounts")

            return Response(200, data=str(poem._id)).to_json()
        else:
            return Response(400, reason="Draft not found in record.").to_json()
    else:
        return Response(400, reason="Publisher account not found in record.").to_json()
    return "200"


"""""""""EDITING POEMS"""""""""


def edit_a_poem(poem_id: str):
    replacement_data = read_request_body(request)
    poem_document = get_poem_document(poem_id)

    # updatable poem attributes
    # -> title
    # -> body
    # -> annotations
    # -> description
    # -> featured poets
    # -> thumbnail
    # -> languages
    # -> collection
    # -> tags

    updatable_attributes = ("title", "body", "annotations", "description", "featured_poets", "thumbnail",
                            "languages", "collection", "tags")
    string_attributes = ("title", "body", "description",
                         "thumbnail", "collection", "languages")

    for attribute in replacement_data:
        if attribute in updatable_attributes:
            if attribute in string_attributes:
                poem_document[attribute] = replacement_data[attribute]
                # TODO: Be sure to handle a situation where annotations are affected by the body change
                # For the body change also re-calculate the read time
                if attribute == "body":
                    poem_document[attribute] = replacement_data[attribute]
                    poem_document["read_time"] = readtime.of_text(
                        poem_document[attribute]).__str__()
            else:
                if attribute == "featured_poets":
                    poem_document[attribute] = []
                    for index, featured_poet in enumerate(replacement_data[attribute]):
                        poem_document[attribute].append(
                            bson.objectid.ObjectId(poem_document[attribute][index]))

                elif attribute == "tags":
                    poem_document[attribute] = []
                    for tag in replacement_data[attribute]:
                        existing_tag = get_tag_document(tag)
                        if existing_tag:
                            if poem_document["_id"] not in existing_tag["publishes"]:
                                existing_tag["publishes"].append(
                                    poem_document["_id"])
                                existing_tag["publishes_count"] = len(
                                    existing_tag["publishes"])
                                update_tag_document(existing_tag)
                            poem_document[attribute].append(
                                existing_tag["_id"])
                        else:
                            tag_data = Tag(tag)
                            existing_tag = _Tag(**tag_data)
                            existing_tag.publishes.append(poem_document["_id"])
                            existing_tag.publishes_count = len(
                                existing_tag.publishes_count)
                            existing_tag.save()
                            poem_document[attribute].append(existing_tag._id)
                # TODO: Annotations edits will go here

    is_poem_saved = update_poem_document(poem_changes=poem_document)
    if is_poem_saved:
        return Response(200).to_json()
    else:
        return Response(500, reason="Something went wrong while saving your poem.").to_json()


"""""""""DELETING POEMS"""""""""


def delete_poem(poem_id):
    auth_data = g.my_request_var["payload"]
    account = get_from_collection(
        search_value=auth_data["email_address"], search_key="email_address", collection_name="accounts")
    poem_id = bson.objectid.ObjectId(poem_id)

    if account:
        poem = get_poem_document(str(poem_id))
        if poem:
            if account["_id"] == poem["author"]:
                is_poem_deleted = delete_from_collection(
                    search_value=poem_id, search_key="_id", collection_name="poems")
                if is_poem_deleted:
                    # also delete the comments the were made for the poem
                    is_comments_deleted = delete_from_collection(
                        search_value=poem_id, search_key="of", collection_name="comments")
                    if is_comments_deleted:
                        return Response(200).to_json()
                    else:
                        return Response(500, reason="Something went while deleting comments in the poem.").to_json()
                else:
                    return Response(500, reason="Something went wrong while deleting poem.").to_json()
            else:
                return Response(403, reason="You are not allowed to carry-out this action.").to_json()
        else:
            return Response(404, reason="Poem was not found in record.").to_json()
    else:
        return Response(404, reason="Your account was not found in record.").to_json()


"""""""""REACTING TO POEMS"""""""""


def react_to_poem(poem_id, reaction):
    auth_data = g.my_request_var["payload"]
    reactor = get_from_collection(
        search_value=auth_data["email_address"], search_key="email_address", collection_name="accounts")
    if reactor:
        poem = get_poem_document(poem_id)
        if poem:
            reactor_id = bson.objectid.ObjectId(reactor["_id"])
            # reset the reaction state of the user, if any
            if reactor_id in poem["likes"]:
                poem["likes"].remove(reactor_id)
                poem["likes_count"] = len(poem["likes"])
            elif reactor_id in poem["dislikes"]:
                poem["dislikes"].remove(reactor_id)
                poem["dislikes_count"] = len(poem["dislikes"])

            if reaction == "like":
                poem["likes"].append(reactor_id)
                poem["likes_count"] = len(poem["likes"])
            elif reaction == "dislike":
                poem["dislikes"].append(reactor_id)
                poem["dislikes_count"] = len(poem["dislikes"])

            is_poem_saved = update_poem_document(poem_changes=poem)
            if is_poem_saved:
                return Response(200).to_json()
            else:
                return Response(500, reason="Something went wrong while saving the poem.").to_json()
        else:
            return Response(404, reason="Poem was not found in record. It may have been deleted.").to_json()
    else:
        return Response(404, reason="Your account was not found in record.").to_json()


# Be able to rank poems from the most liked to the most disliked for a user that is not logged in
def unauthenticated_poemsfeed():
    poems = get_from_collection(
        search_value=None, collection_name="poems", return_all=True)
    recommended_poems = []

    # Determine an average score of the poems in record
    base_score = 0
    avg_scores = dict(likes_count=base_score, dislikes_count=base_score,
                      comments_count=base_score, shares_count=base_score, reports_count=base_score)
    scores_count = base_score

    for poem in poems:
        avg_scores["likes_count"] += poem["likes_count"]
        # avg_scores["dislikes_count"] += poem["dislikes_count"]
        avg_scores["comments_count"] += poem["comments_count"]
        avg_scores["shares_count"] += poem["shares_count"]
        avg_scores["reports_count"] += poem["reports_count"]

        scores_count += 1

    # Use an average score to determine which poems to recommend
    for poem in poems:
        poem["author"] = str(poem["author"])
        poem = Poem.to_dict(poem)

        for avg_param in avg_scores:
            avg = avg_scores[avg_param] / scores_count
            avg_score_difference = abs(avg - poem[avg_param])

            if poem not in recommended_poems:
                if avg_score_difference >= 100:
                    recommended_poems.append(poem)

    return Response(200, data=recommended_poems).to_json()


"""DRAFTING POEMS"""


def create_a_draft():
    auth_data = g.my_request_var["payload"]
    author = get_from_collection(
        search_value=auth_data["email_address"], search_key="email_address", collection_name="accounts")
    if author:
        request_data = read_request_body(request=request)
        if request_data:
            draft = get_from_collection(search_value=request_data.get(
                "did"), search_key="did", collection_name="drafts")
            if draft:
                draft = {**draft, **request_data}
                is_draft_saved = update_a_document(
                    document_changes=draft, collection_name="drafts")
                if is_draft_saved:
                    return Response(200).to_json()
                else:
                    return Response(500, reason="Something went wrong while saving the draft.")
            else:
                draft_data = Draft(
                    {**request_data, "owner": author["email_address"]})
                draft = _Draft(**draft_data.__dict__)
                author["drafts"].append(draft._id)
                is_author_saved = update_a_document(
                    document_changes=author, collection_name="accounts")
                if is_author_saved:
                    draft.save()
                    return Response(200).to_json()
                else:
                    return Response(500, reason="Something went wrong while saving the draft.").to_json()
        else:
            return Response(400, reason="Incomplete request. No data was received.").to_json()
    else:
        return Response(403, reason="You are not allowed to carry out this action.").to_json()


"""GETTING ALL THE DRAFTS OF A POET"""


def get_drafts():
    auth_data = g.my_request_var["payload"]
    drafts = get_from_collection(
        search_value=auth_data["email_address"], search_key="owner", collection_name="drafts", return_all=True)

    for draft in drafts:
        draft["_id"] = str(draft["_id"])
        draft = Draft.to_dict(draft)

    return Response(200, data=drafts).to_json()


"""GETTING A DRAFT POEM"""


def get_a_draft(did: str) -> str:
    auth_data = g.my_request_var["payload"]
    author = get_from_collection(
        search_value=auth_data["email_address"], search_key="email_address", collection_name="accounts")
    if author:
        draft_document = get_from_collection(
            search_value=did, search_key="did", collection_name="drafts")
        print(draft_document)
        if draft_document:
            draft_document = Poem.to_dict(draft_document)
            return Response(200, data=draft_document).to_json()
        else:
            return Response(404, reason="Draft does not exist in record.").to_json()
    else:
        return Response(404, reason="Original author was not found in record.").to_json()
        return Response(404, reason="Original author was not found in record.").to_json()
