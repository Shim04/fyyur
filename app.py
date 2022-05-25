#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
from operator import itemgetter
from typing import final
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort, jsonify
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from models import *
from operator import itemgetter

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

# displays list of venues
@app.route('/venues')
def venues():
    data = []
    # get all venues
    venues = Venue.query.all()

    # get all locations and add to data
    locations = set()
    for venue in venues:
        locations.add((venue.city, venue.state))

    # sort the list by state first and then the city
    locations = list(locations)
    locations.sort(key=itemgetter(1, 0))

    for location in locations:
        data.append({
            'city': location[0],
            'state': location[1],
            'venues': []
        })

    curr = datetime.now()
    # add venue to data
    for venue in venues:
        num_upcoming_shows = 0
        shows = Show.query.filter_by(venue_id=venue.id).all()

        # calculate # of upcoming show
        for show in shows:
            if show.start_time > curr:
                num_upcoming_shows += 1

        for location in data:
            if location['city'] == venue.city and location['state'] == venue.state:
                location['venues'].append({
                    'id': venue.id,
                    'name': venue.name,
                    'num_upcoming_shows': num_upcoming_shows
                })

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term', '').strip()
    venues = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
    response = {
        'count': len(venues),
        'data': [{'id': venue.id, 'name': venue.name} for venue in venues]
    }
    return render_template('pages/search_venues.html', results=response, search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)
    genres = [genre.name for genre in venue.genres]
    curr = datetime.now()
    past_shows = []
    upcoming_shows = []
    for show in venue.shows:
        artist = show.artist
        show_detail = {
            'artist_id': artist.id,
            'artist_name': artist.name,
            'artist_image_link': artist.image_link,
            'start_time': format_datetime(str(show.start_time))
        }
        if show.start_time <= curr:
            past_shows.append(show_detail)
        else:
            upcoming_shows.append(show_detail)

    data = {
        'id': venue.id,
        'name': venue.name,
        'genres': genres,
        'address': venue.address,
        'city': venue.city,
        'state': venue.state,
        'phone': venue.phone,
        'website': venue.website_link,
        'facebook_link': venue.facebook_link,
        'seeking_talent': venue.seeking_talent,
        'seeking_description': venue.seeking_description,
        'image_link': venue.image_link,
        'past_shows': past_shows,
        'upcoming_shows': upcoming_shows,
        'past_shows_count': len(past_shows),
        'upcoming_shows_count': len(upcoming_shows)
    }
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # get the form data
    form = VenueForm(request.form)
    print(form)
    print(type(form.name.data))
    print(form.genres.data)
    print(request.form['name'])
    name = form.name.data
    city = form.city.data
    state = form.state.data
    address = form.address.data
    phone = form.phone.data
    genres = form.genres.data
    image_link = form.image_link.data
    facebook_link = form.facebook_link.data
    website_link = form.website_link.data
    seeking_talent = form.seeking_talent.data
    seeking_description = form.seeking_description.data

    # check if errors in form validation
    if not form.validate():
        flash(form.errors)
        return redirect(url_for('create_venue_submission'))
    else:
        error = False
        try:
            venue = Venue(name=name, city=city, state=state, address=address, phone=phone, seeking_talent=seeking_talent,
                          seeking_description=seeking_description, image_link=image_link, website_link=website_link, facebook_link=facebook_link)

            # create genres
            for genre in genres:
                print(genre)
                fetch_genre = Genre.query.filter_by(name=genre).one_or_none()
                if fetch_genre:
                    venue.genres.append(fetch_genre)
                else:
                    # return none, create
                    new_genre = Genre(name=genre)
                    db.session.add(new_genre)
                    venue.genres.append(new_genre)

            db.session.add(venue)
            db.session.commit()
        except Exception as e:
            error = True
            print(f'Exception {e} in create venue')
            db.session.rollback()
        finally:
            db.session.close()

        if not error:
            flash('Venue ' + name + ' was successfully listed!')
            return redirect(url_for('index'))
        else:
            flash('An error occurred. Venue ' + name + ' could not be listed.')
            abort(500)


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    error = False
    try:
        venue = Venue.query.get(venue_id)
        venue_name = venue.name
        for show in venue.shows:
            db.session.delete(show)
        db.session.delete(venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()

    if not error:
        flash('Venue ' + venue_name + ' was deleted')
        return jsonify({
            'deleted': True,
            'url': url_for('venues')
        })
    else:
        flash('An error occurred. Venue ' +
              venue_name + ' could not be deleted.')
        abort(500)

#  Artists
#  ----------------------------------------------------------------

# displays list of artists


@app.route('/artists')
def artists():
    artists = Artist.query.order_by(Artist.name).all()
    data = []

    for artist in artists:
        data.append({
            'id': artist.id,
            'name': artist.name
        })
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term', '').strip()
    artists = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
    response = {
        'count': len(artists),
        'data': [{'id': artist.id, 'name': artist.name} for artist in artists]
    }
    return render_template('pages/search_artists.html', results=response, search_term=search_term)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = Artist.query.get(artist_id)
    genres = [genre.name for genre in artist.genres]
    past_shows = []
    upcoming_shows = []
    curr = datetime.now()
    for show in artist.shows:
        venue = show.venue
        show_detail = {
            'venue_id': venue.id,
            'venue_name': venue.name,
            'venue_image_link': venue.image_link,
            'start_time': format_datetime(str(show.start_time))
        }
        if show.start_time <= curr:
            past_shows.append(show_detail)
        else:
            upcoming_shows.append(show_detail)

    data = {
        'id': artist.id,
        'name': artist.name,
        'genres': genres,
        'city': artist.city,
        'state': artist.state,
        'phone': artist.phone,
        'website': artist.website_link,
        'facebook_link': artist.facebook_link,
        'seeking_venue': artist.seeking_venue,
        'seeking_description': artist.seeking_description,
        'image_link': artist.image_link,
        'past_shows': past_shows,
        'upcoming_shows': upcoming_shows,
        'past_shows_count': len(past_shows),
        'upcoming_shows_count': len(upcoming_shows)
    }
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.get(artist_id)
    form = ArtistForm(obj=artist)
    artist_data = {
        'id': artist_id,
        'name': artist.name
    }
    return render_template('forms/edit_artist.html', form=form, artist=artist_data)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    form = ArtistForm(request.form)
    name = form.name.data
    city = form.city.data
    state = form.state.data
    phone = form.phone.data
    genres = form.genres.data
    image_link = form.image_link.data
    facebook_link = form.facebook_link.data
    website_link = form.website_link.data
    seeking_venue = form.seeking_venue.data
    seeking_description = form.seeking_description.data

    # redirect if errors in form validation
    if not form.validate():
        flash(form.errors)
        return redirect(url_for('edit_artist_submission', artist_id=artist_id))
    else:
        error = False
        try:
            artist = Artist.query.get(artist_id)
            artist.name = name
            artist.city = city
            artist.state = state
            artist.phone = phone
            artist.image_link = image_link
            artist.facebook_link = facebook_link
            artist.website_link = website_link
            artist.seeking_venue = seeking_venue
            artist.seeking_description = seeking_description

            artist.genres.clear()
            for genre in genres:
                fetch_genre = Genre.query.filter_by(name=genre).one_or_none()
                if fetch_genre:
                    artist.genres.append(fetch_genre)
                else:
                    new_genre = Genre(name=genre)
                    db.session.add(new_genre)
                    artist.genres.append(new_genre)

            db.session.commit()
        except Exception as e:
            error = True
            print(f'Exception {e} in edit artist')
            db.session.rollback()
        finally:
            db.session.close()

        if not error:
            flash('The Artist ' + name + ' has been successfully updated!')
            return redirect(url_for('show_artist', artist_id=artist_id))
        else:
            flash('An error has occured and update failed')
            abort(500)


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue = Venue.query.get(venue_id)
    form = VenueForm(obj=venue)
    venue = {
        "id": venue_id,
        "name": venue.name
    }
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    form = VenueForm(request.form)
    name = form.name.data
    city = form.city.data
    state = form.state.data
    address = form.address.data
    phone = form.phone.data
    genres = form.genres.data
    image_link = form.image_link.data
    facebook_link = form.facebook_link.data
    website_link = form.website_link.data
    seeking_talent = form.seeking_talent.data
    seeking_description = form.seeking_description.data

    if not form.validate():
        flash(form.errors)
        return redirect(url_for('edit_venue_submission', venue_id=venue_id))
    else:
        error = False

        try:
            venue = Venue.query.get(venue_id)
            venue.name = name
            venue.city = city
            venue.state = state
            venue.address = address
            venue.phone = phone
            venue.image_link = image_link
            venue.facebook_link = facebook_link
            venue.website_link = website_link
            venue.seeking_talent = seeking_talent
            venue.seeking_description = seeking_description

            venue.genres.clear()
            for genre in genres:
                fetch_genre = Genre.query.filter_by(name=genre).one_or_none()
                if fetch_genre:
                    venue.genres.append(fetch_genre)
                else:
                    new_genre = Genre(name=genre)
                    db.session.add(new_genre)
                    venue.genres.append(new_genre)

            db.session.commit()
        except Exception as e:
            error = True
            print(f'Exception "{e}" in edit venue')
            db.session.rollback()
        finally:
            db.session.close()

        if not error:
            flash('The Venue ' + name + ' has been successfully updated!')
            return redirect(url_for('show_venue', venue_id=venue_id))
        else:
            flash('An error has occured and update failed')
            abort(500)


#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # get the form data
    form = ArtistForm(request.form)
    name = form.name.data
    city = form.city.data
    state = form.state.data
    phone = form.phone.data
    genres = form.genres.data
    image_link = form.image_link.data
    facebook_link = form.facebook_link.data
    website_link = form.website_link.data
    seeking_venue = form.seeking_venue.data
    seeking_description = form.seeking_description.data

    # check if errors in form validation
    if not form.validate():
        flash(form.errors)
        return redirect(url_for('create_artist_submission'))
    else:
        error = False
        try:
            artist = Artist(name=name, city=city, state=state, phone=phone, seeking_venue=seeking_venue,
                            seeking_description=seeking_description, image_link=image_link, website_link=website_link, facebook_link=facebook_link)

            # create genres
            for genre in genres:
                fetch_genre = Genre.query.filter_by(name=genre).one_or_none()
                if fetch_genre:
                    artist.genres.append(fetch_genre)
                else:
                    # return none, create
                    new_genre = Genre(name=genre)
                    db.session.add(new_genre)
                    artist.genres.append(new_genre)

            db.session.add(artist)
            db.session.commit()
        except Exception as e:
            error = True
            print(f'Exception {e} in create artist')
            db.session.rollback()
        finally:
            db.session.close()

        if not error:
            flash('Artist ' + name +
                  ' was successfully listed!')
            return redirect(url_for('index'))
        else:
            flash('An error occurred. Artist ' +
                  name + ' could not be listed.')
            abort(500)


@app.route('/artists/<int:artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
    error = False
    try:
        artist = Artist.query.get(artist_id)
        artist_name = artist.name
        for show in artist.shows:
            db.session.delete(show)
        db.session.delete(artist)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()

    if not error:
        flash('Artist ' + artist_name + ' was deleted')
        return jsonify({
            'deleted': True,
            'url': url_for('artists')
        })
    else:
        flash('An error occured and artist ' +
              artist_name + 'could not be deleted.')
        abort(500)


#  Shows
#  ----------------------------------------------------------------

# displays list of shows at /shows
@app.route('/shows')
def shows():
    shows = Show.query.order_by(db.desc(Show.start_time)).all()
    data = []
    for show in shows:
        data.append({
            'venue_id': show.venue_id,
            'venue_name': show.venue.name,
            'artist_id': show.artist_id,
            'artist_name': show.artist.name,
            'artist_image_link': show.artist.image_link,
            'start_time': format_datetime(str(show.start_time))
        })
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create', methods=['GET'])
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    error = False
    try:
        form = ShowForm(request.form)
        show = Show(
            artist_id=form.artist_id.data,
            venue_id=form.venue_id.data,
            start_time=form.start_time.data
        )
        db.session.add(show)
        db.session.commit()
    except Exception as e:
        error = True
        print(f'Exception "{e}" in create show')
        db.session.rollback()
    finally:
        db.session.close()

    if not error:
        flash('Show was successfully listed!')
        return redirect(url_for('shows'))
    else:
        flash('An error occurred. Show could not be listed.')
        abort(500)


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
