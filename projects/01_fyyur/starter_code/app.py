#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
from operator import itemgetter
import sys
import dateutil.parser
import babel
from flask import Flask, abort, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment

import logging
from logging import Formatter, FileHandler
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import Form
from sqlalchemy import DateTime
from forms import *
from flask_migrate import Migrate
from shared import db
from models import Venue, Show, Artist
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)

moment = Moment(app)
app.config.from_object('config')

db.init_app(app)

# TODO: connect to a local postgresql database
migrate = Migrate(app, db)
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


db = SQLAlchemy(app)


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

db.create_all()
#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    venues = Venue.query.group_by(Venue.id, Venue.state, Venue.city).all()
    data = []
    for venue in venues:
        upcoming_shows = Show.query.filter(
            Show.start_time > datetime.now()).all()
        venue_list = {
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": len(upcoming_shows)
        }
        states = {
            "city": venue.city,
            "state": venue.state,
            "venues": [venue_list]
        }
        data.append(states)

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():

    search_query = request.form.get('search_term', '').strip()

    venues = Venue.query.filer(
        Venue.name.ilike('%' + search_query + '%')).all()

    venue_list = []
    for venue in venues:
        venue_show = Show.query.filter_by(venue_id=venue.id).all()
        num_upcoming_show = 0
        for show in venue_show:
            if show.start_time > datetime.now():
                num_upcoming_show += 1

        venue_list.append({
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": num_upcoming_show
        })

    response = {
        "count": len(venues),
        "data": venue_list
    }

    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)

    if not venue:
        return redirect(url_for('index'))
    else:
        shows = Show.query.all()
        past_shows = []
        upcoming_shows = []
    for show in shows:
        flash(show)
        show_detail = {
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "start_time": show.start_time
        }

    if show.start_time < datetime.now():
        past_shows.append(show_detail)
    if show.start_time > datetime.now():
        upcoming_shows.append(show_detail)

    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website_link,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link.strip('"'),
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    flash(data)

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

    error = False
    form = VenueForm(request.form)

    try:
        form.validate()
        newVenue = Venue(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            address=form.address.data,
            phone=form.phone.data,
            genres=form.genres.data,
            image_link=form.image_link.data,
            facebook_link=form.facebook_link.data,
            website_link=form.website_link.data,
            seeking_talent=form.seeking_talent.data,
            seeking_description=form.seeking_description.data)
        db.session.add(newVenue)
        db.session.commit()

        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info)
        flash('error has occured. Venue ' +
              request.form['name'] + 'Could not be listed.')
    finally:
        db.session.close()
        if error == True:
            abort(400)
        else:
            return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    venue = Venue.query.get(venue_id)
    if not venue:
        return redirect(url_for('index'))
    else:
        error = False
        venue_name = venue.name
        try:
            db.session.delete(venue)
            db.session.commit()
        except:
            error = True
            db.session.rollback()
        finally:
            db.session.close()
        if error:
            flash('An error occured. Could not delete ' + venue_name)
            print(sys.exc_info)
            abort(500)
        else:
            return render_template('pages/home.html')


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    all_artist = Artist.query.order_by(Artist.name).all()
    data = []

    for artist in all_artist:
        artist_list = {
            "id": artist.id,
            "name": artist.name
        }
        data.append(artist_list)

    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():

    search_query = request.form.get('search_term', '').strip()

    artist_list = Artist.query.filter(Artist.name.ilike(
        '%' + search_query + '%')).order_by(Artist.name).all()

    artists = []
    for artist in artist_list:
        artist_show = Show.query.filter_by(artist_id=artist.id).all()
        num_upcoming = 0
        for show in artist_show:
            if show.start_time > datetime.now():
                num_upcoming += 1

        artists.append({
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_show": num_upcoming
        })
    response = {
        "count": len(artist_list),
        "data": artists
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    get_artist = Artist.query.get(artist_id)
    flash(get_artist)
    if not get_artist:
        return redirect(url_for('index'))
    else:

        genres = [genre.name for genre in get_artist.genres]
        flash(genres)
        past_show = []
        upcoming_shows = []
        num_past_show = 0
        num_upcoming_show = 0
        shows = Show.query.all()
        for show in shows:
            if show.start_time > datetime.now():
                num_upcoming_show += 1
                upcoming_shows.append({
                    "venue_id": show.venue_id,
                    "venue_name": show.venue_name,
                    "venue_image_link": show.venue.image_link,
                    "start_time": format_datetime(str(show.start_time))
                })
            if show.start_time < datetime.now():
                num_past_show = +1
                past_show.append({
                    "venue_id": show.venue_id,
                    "venue_name": show.venue_name,
                    "venue_image_link": show.venue.image_link,
                    "start_time": format_datetime(str(show.start_time))
                })
        data = {
            "id": artist_id,
            "name": get_artist.name,
            "genres": genres,
            "address": get_artist.address,
            "city": get_artist.city,
            "state": get_artist.state,
            "phone": get_artist.phone,
            "website": get_artist.website,
            "facebook_link": get_artist.facebook_link,
            "seeking_venue": get_artist.seeking_venue,
            "seeking_description": get_artist.seeking_description,
            "image_link": get_artist.image_link,
            "past_shows": past_show,
            "past_shows_count": num_past_show,
            "upcoming_shows": upcoming_shows,
            "upcoming_shows_count": num_upcoming_show
        }

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.get(artist_id)
    if not artist:
        return redirect(url_for('index'))
    else:

        form = ArtistForm(item=artist)

    artist = {
        "id": artist_id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website_link": artist.website_link,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link
    }

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    form = ArtistForm()
    name = form.name.data
    genres = form.genres.data
    city = form.city.data
    state = form.state.data
    phone = form.phone.data
    website_link = form.website_link.data
    facebook_link = form.facebook_link.data
    seeking_venue = form.seeking_venue.data
    seeking_description = form.seeking_description.data
    image_link = form.image_link.data

    form.validate()
    try:

        get_artist = Artist.query.get(artist_id)
        get_artist.name = name
        get_artist.genres = genres
        get_artist.city = city
        get_artist.state = state
        get_artist.phone = phone
        get_artist.website_link = website_link
        get_artist.facebook_link = facebook_link
        get_artist.seeking_venue = seeking_venue
        get_artist.seeking_description = seeking_description
        get_artist.image_link = image_link

        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue = Venue.query.get(venue_id)
    if not venue:
        return redirect(url_for('index'))
    else:
        form = VenueForm(item=venue)

        venue = {
            "id": venue_id,
            "name": venue.name,
            "genres": venue.genres,
            "city": venue.city,
            "state": venue.state,
            "phone": venue.phone,
            "website_link": venue.website_link,
            "facebook_link": venue.facebook_link,
            "seeking_talent": venue.seeking_talent,
            "seeking_description": venue.seeking_description,
            "image_link": venue.image_link
        }

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    form = VenueForm()
    form.validate()
    name = form.name.data
    genres = form.genres.data
    city = form.city.data
    state = form.state.data
    phone = form.phone.data
    website_link = form.website_link.data
    facebook_link = form.facebook_link.data
    seeking_talent = form.seeking_talent.data
    seeking_description = form.seeking_description.data
    image_link = form.image_link.data

    try:

        get_venue = Venue.query.get(venue_id)
        get_venue.name = name
        get_venue.genres = genres
        get_venue.city = city
        get_venue.state = state
        get_venue.phone = phone
        get_venue.website_link = website_link
        get_venue.facebook_link = facebook_link
        get_venue.seeking_talent = seeking_talent
        get_venue.seeking_description = seeking_description
        get_venue.image_link = image_link

        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()

    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    error = False
    form = ArtistForm(request.form)

    try:
        form.validate()
        artist = Artist(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            phone=form.phone.data,
            genres=form.genres.data,
            image_link=form.image_link.data,
            facebook_link=form.facebook_link.data,
            website_link=form.website_link.data,
            seeking_venue=form.seeking_venue.data,
            seeking_description=form.seeking_description.data)
        db.session.add(artist)
        db.session.commit()

        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info)
        flash('error has occured. Artist ' +
              request.form['name'] + 'Could not be listed.')
    finally:
        db.session.close()
        if error == True:
            abort(400)
        else:
            return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():

    data = []
    shows = Show.query.all()

    for show in shows:
        data.append({
            "venue_id": show.venue.id,
            "venue_name": show.venue.name,
            "artist_id": show.artist.id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": str(show.start_time)
        })
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    error = False
    form = ShowForm(request.form)

    try:

        newShow = Show(
            artist_id=form.artist_id.data,
            venue_id=form.venue_id.data,
            start_time=form.start_time.data)
        db.session.add(newShow)
        db.session.commit()

        flash('Show was successfully listed!')
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info)
        flash('error has occured. Show ' +
              request.form['name'] + 'Could not be listed.')
    finally:
        db.session.close()
        if error == True:
            abort(400)
        else:
            return render_template('pages/home.html')


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
    app.run(host="0.0.0.0", port=5000)

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)
'''
