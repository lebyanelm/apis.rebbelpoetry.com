# dependencies
import os
import sys
import mongoengine
import readtime
import random
import bson
from flask import request, g


# models
from models.poem import Poem
from models.response import Response
from models.tag import Tag
from models.draft import Draft
from models.account import Account


# helpers
from helpers.request import read_request_body
from helpers.poems import get_poem_document, update_poem_document, get_tag_document, update_tag_document
from helpers.database import get_from_collection, update_a_document, delete_from_collection
from helpers.authentication import decode_authentication_token


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


def react_to_poem(poem_id):
    auth_data = g.my_request_var["payload"]
    reactor = get_from_collection(
        search_value=auth_data["email_address"], search_key="email_address", collection_name="accounts")
    if reactor:
        poem = get_poem_document(poem_id)
        if poem:
            reactor_id = bson.objectid.ObjectId(reactor["_id"])
            # reset the reaction state of the user, if any
            if not (reactor_id in poem["likes"]):
                poem["likes"].append(reactor_id)
                poem["likes_count"] = len(poem["likes"])
            else:
                poem["likes"].remove(reactor_id)
                poem["likes_count"] = len(poem["likes"])

            is_poem_saved = update_poem_document(poem_changes=poem)
            if is_poem_saved:
                poem_likes = []
                for like in poem["likes"]:
                    poem_likes.append(str(like))
                return Response(200, data=dict(likes_count=poem["likes_count"], likes=poem_likes)).to_json()
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
        avg_scores["dislikes_count"] += poem["dislikes_count"]
        avg_scores["comments_count"] += poem["comments_count"]
        avg_scores["shares_count"] += poem["shares_count"]
        avg_scores["reports_count"] += poem["reports_count"]

        scores_count += 1

    # Use an average score to determine which poems to recommend
    for poem in poems:
        if poem.get("author"):
            poem["author"] = str(poem["author"])
        poem = Poem.to_dict(poem)

        for avg_param in avg_scores:
            avg = avg_scores[avg_param] / scores_count
            avg_score_difference = abs(avg - poem[avg_param])

            print("POEM AVG:", avg, avg_score_difference)

            if poem not in recommended_poems:
                if avg_score_difference >= 20:
                    recommended_poems.append(poem)

    print(len(recommended_poems), "RECOMMENDED POEMS")
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


"""SEARCHING A POEM WITH A KEYWORD"""


def find_poem_from_keyword(keyword: str) -> str:
    if keyword and len(keyword):
        poems = get_from_collection(
            search_value="", collection_name="poems", return_all=True)
        authors = get_from_collection(
            search_value="", collection_name="accounts", return_all=True)

        # results to be returned
        poem_results = []
        poem_related_authors = []
        author_results = []

        # Most params in the poem have other nested objects, this should help in
        # digging deeper still in search of a string or number
        def traverse_dict(object, original_object, search_word, results):
            keys = object.keys() if type(object) == dict else range(len(object))

            for object_key in keys:
                if type(object[object_key]) in [str, dict, list, int, float]:

                    # Continue traversing deeper if type is list or dict
                    if type(object[object_key]) in [dict, list]:
                        traverse_dict(
                            object[object_key], original_object, search_word, results)
                    else:

                        # Compare the keyword and they object key value to find a match
                        print("LOG: [SEARCH]: ", search_word,
                              str(object[object_key]))
                        if search_word in str(object[object_key]).lower():

                            # Check if the item has not been added yet to prevent duplicate results
                            if len(results):
                                print(results)
                                for result_item in results:
                                    is_found_duplicate = False
                                    if str(result_item.get("_id")) == str(original_object.get("_id")):
                                        is_found_duplicate = True

                                print(
                                    "LOG: [SEARCH]: IS DUPLICATE FOUND?: ", is_found_duplicate)
                                if is_found_duplicate != True:
                                    results.append(original_object)
                                    print("LOG: [SEARCH]: POEM AUTHOR ID",
                                          original_object.get("author"))
                                    if original_object.get("author"):
                                        print(
                                            "LOG: [SEARCH]: APPENDING RELATED AUTHOR ID:", original_object.get("author"))
                                        if original_object.get("author") not in author_results:
                                            author_results.append(
                                                original_object.get("author"))
                                    # No need to look into the rest of the object becuase
                                    # duplcates are not accepted anyways.
                                    break
                            else:
                                results.append(original_object)
                                print("LOG: [SEARCH]: POEM AUTHOR ID",
                                      original_object.get("author"))
                                if original_object.get("author"):
                                    print(
                                        "LOG: [SEARCH]: APPENDING RELATED AUTHOR ID:", original_object.get("author"))
                                    if original_object.get("author") not in author_results:
                                        author_results.append(
                                            original_object.get("author"))
                                # No need to look into the rest of the object becuase
                                # duplcates are not accepted anyways.
                                break
                            # Break the top loop. Since the match has been found
                            # and it probably means this part of the code is reached
                            # becuase the result has been appended or ignored becuase of a duplicate.
                            break

        # Search all the poems using the string values in the poem attributes
        for poem_item in poems:
            traverse_dict(poem_item, Poem.to_dict(poem_item),
                          keyword.lower(), poem_results)

        # Search all the authors using the string values in the account attributes
        for author_item in authors:
            traverse_dict(author_item, dict(
                _id=str(author_item.get("_id")),
                username=author_item.get("username"),
                display_name=author_item.get("display_name"),
                display_photo=author_item.get("display_photo")
            ),
                keyword.lower(), poem_related_authors)

        # Search all the authors using the authors whose poems have been found using string value
        # for poem_related_author in poem_related_authors:
        #     print("LOG: [SEARCH]: SEARCHING FOR RELATED AUTHOR",
        #           poem_related_author, type(poem_related_author))

        #     if poem_related_author == "Anonymous":
        #         pass
        #     else:
        #         related_author = get_from_collection(search_value=bson.objectid.ObjectId(poem_related_author),
        #                                              search_key="_id", collection_name="accounts")
        #         print("LOG: [SEARCH]: RELATED AUTHOR:", related_author)
        #         if related_author:
        #             if len(author_results):
        #                 for author_result in author_results:
        #                     is_duplicate_found = False
        #                     if author_result.get("_id") == str(related_author.get("_id")):
        #                         is_duplicate_found = True
        #                     if not is_duplicate_found:
        #                         author_results.append(
        #                             Account.to_dict(related_author))
        #                         break
        #             else:
        #                 author_results.append(Account.to_dict(related_author))

        print(poem_related_authors)
        return Response(200, data=dict(poems=poem_results, authors=poem_related_authors),
                        reason=f"With {len(poem_results) + len(author_results)} results.").to_json()

    else:
        return Response(400, reason="No search keyword was provided.").to_json()

    return Response(500, reason="Something went wrong.").to_json()


"""GETTING A RANDOM POEM"""


def feeling_lucky():
    poems = get_from_collection(
        search_value=None, search_key="_id", collection_name="poems", return_all=True)

    # Get a random position index of the poem to send back
    random_index = random.randint(0, len(poems) - 1)

    if len(poems) > 0:
        poem = Poem.to_dict(poems[random_index])
        if poem.get("author"):
            poem["author"] = str(poem["author"])

        return Response(200, data=poem).to_json()
    else:
        return Response(500, reason="No poems are in record yet.").to_json()


"""""""""BOOKMARK POEMS"""""""""


def bookmark_a_poem():
    auth_data = g.my_request_var["payload"]
    request_data = read_request_body(request)

    # Check if the poem ID has been sent with the request
    if request_data.get("pId") and auth_data.get("email_address"):
        pId = bson.objectid.ObjectId(request_data.get("pId"))
        # Ge the account that sent the request
        account = get_from_collection(search_value=auth_data.get(
            "email_address"), search_key="email_address", collection_name="accounts")
        if account:
            is_bookmark = False
            # Check the poem ID exists in the bookmarked poems
            if pId not in account["bookmarked_poems"]:
                account["bookmarked_poems"].append(pId)
                is_bookmark = True
            else:
                account["bookmarked_poems"].remove(pId)
                is_bookmark = False

            print("Is bookmarked poem:", is_bookmark)

            # Update the changes on the account
            is_updated = update_a_document(
                document_changes=account, collection_name="accounts")
            if is_updated:
                # Update the number on the poem data
                poem_document = get_poem_document(poem_id=pId)
                if poem_document:
                    if is_bookmark:
                        poem_document["bookmarks_count"] = (
                            poem_document["bookmarks_count"] + 1)
                    else:
                        poem_document["bookmarks_count"] = (
                            poem_document["bookmarks_count"] - 1)

                    is_poem_updated = update_poem_document(
                        poem_changes=poem_document)
                    if is_poem_updated:
                        return Response(200, data=dict(bookmarks_count=poem_document["bookmarks_count"], is_bookmark=is_bookmark)).to_json()
                    else:
                        return Response(500, reason="Something went wrong while saving the poem.").to_json()
                else:
                    return Response(404, reason="The poem was not found in record.").to_json()
        else:
            return Response(404, reason="Your account was not found in record.").to_json()
    else:
        if request_data.get("email_address") == None:
            return Response(400, reason="Invalid authentication provided. Please login again to fix this issue.").to_json()
        else:
            return Response(400, reason="The PoemID was not sent with the request.").to_json()

    return Response(200).to_json()


"""GETTING POEM TAGS"""


def get_poem_tags(tags: str) -> str:
    tags_split = tags.split(",")
    response_tags = list()

    # In means of tracking what type of poems the user clicks and likes
    reader_track = request.headers.get("User-Track")
    reader = None
    if reader_track and len(reader_track) > 0:
        # Tokens format = Bearer <TOKEN>, remove the "Bearer"
        reader_track = reader_track.split(" ")
        if len(reader_track) > 1:
            reader_track = decode_authentication_token(reader_track[1])
            reader = get_from_collection(search_value=reader_track.get("email_address"),
                                         search_key="email_address", collection_name="accounts")

    for tag in tags_split:
        tag_document = get_from_collection(search_value=bson.objectid.ObjectId(
            tag), search_key="_id", collection_name="tags")
        if tag_document:
            tag_document["reads_count"] = tag_document["reads_count"] + 1
            if reader and reader.get("_id") not in tag_document["reads"]:
                tag_document["reads"].append(reader.get("_id"))
                reader["interests"].append(tag_document["_id"])

        response_tags.append(
            dict(_id=str(tag_document["_id"]), name=tag_document["name"].capitalize()))

    return Response(200, data=response_tags).to_json()
