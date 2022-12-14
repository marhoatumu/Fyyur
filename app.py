#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
import sys
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort, jsonify
from flask_moment import Moment
from datetime import datetime
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import db, Artist, Venue, Shows
import collections
collections.Callable = collections.abc.Callable

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
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

@app.route('/venues')
def venues():
  show_venues = Venue.query.distinct(Venue.city, Venue.state).all()
  data = []
  for show_venue in show_venues:
    location = {"city": show_venue.city, "state": show_venue.state}
    venues = Venue.query.filter_by(city=show_venue.city, state=show_venue.state).all()
    layout_venues = []
    for venue in venues:
      layout_venues.append({"id": venue.id, "name": venue.name, "num_upcoming_shows": len(list(filter(lambda x: x.start_time > datetime.now(), venue.shows)))})  
    location["venues"] = layout_venues
    data.append(location)

  #TODO: replace with real venues data.
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

  search_term = request.form.get("search_term", "")

  search_results = {}
  venues = list(Venue.query.filter(Venue.name.ilike(f"%{search_term}%")).all())
  search_results["count"] = len(venues)
  search_results["data"] = []

  for venue in venues:
    each_venue = {
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": len(list(filter(lambda x: x.start_time > datetime.now(), venue.shows)))
    }
    search_results["data"].append(each_venue)

  return render_template('pages/search_venues.html', results=search_results, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.get(venue_id)
  setattr(venue, "genres", venue.genre.split(", "))
  today = datetime.now()

  # get information about upcoming shows
  upcoming_shows_query = db.session.query(Shows).join(Artist).filter(Shows.venue_id==venue_id).filter(Shows.start_time>today).all()
  upcoming_shows = [] 
  for show in upcoming_shows_query:
    info = {"artist_name": show.artists.name, "artist_id": show.artists.id, "artist_image_link": show.artists.image_link, "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M:%S")}
    upcoming_shows.append(info)
  setattr(venue, "upcoming_shows", upcoming_shows)    
  setattr(venue,"upcoming_shows_count", len(upcoming_shows))

  # get information about past shows
  past_shows_query = db.session.query(Shows).join(Artist).filter(Shows.venue_id==venue_id).filter(Shows.start_time<today).all()
  past_shows = []
  for show in past_shows_query:
    info = {"artist_name": show.artists.name, "artist_id": show.artists.id, "artist_image_link": show.artists.image_link, "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M:%S")}
    past_shows.append(info)
  setattr(venue, "past_shows", past_shows)    
  setattr(venue,"past_shows_count", len(past_shows))

  return render_template('pages/show_venue.html', venue=venue)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead

  # TODO: modify data to be the data object returned from db insertion
  form = VenueForm(request.form)
  if form.validate():
    try:
      name = form.name.data
      city = form.city.data
      state = form.state.data
      address = form.address.data
      phone = form.phone.data
      genre = " ".join(form.genres.data)
      image_link = form.image_link.data
      facebook_link = form.facebook_link.data
      website_link = form.website_link.data
      seeking_talent = form.seeking_talent.data
      seeking_description = form.seeking_description.data
      create_venue = Venue(name = name, city = city, state = state, address = address, phone = phone, genre = genre, image_link = image_link, facebook_link = facebook_link, website_link = website_link, seeking_talent = seeking_talent, seeking_description = seeking_description)
      db.session.add(create_venue)
      db.session.commit()
      # on successful db insert, flash success
      flash('Venue ' + request.form['name'] + ' was successfully listed!')

    except:
      db.session.rollback()
      # TODO: on unsuccessful db insert, flash an error instead.
      # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
      # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
      print(sys.exc_info())
    finally:
      db.session.close()
  else:
    flash('An error occurred. Venue ' + request.form['name'] +  ' could not be listed. Please check your form data and try again')
    flash (form.errors)
    
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
    flash("Venue " + venue.name + " was deleted successfully!")
  except:
      db.session.rollback()
      print(sys.exc_info())
      flash("Venue was not deleted successfully.")
  finally:
      db.session.close()
      
  return render_template('venues.html')
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = db.session.query(Artist.id, Artist.name).all()
  
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form.get("search_term", "")
  search_results = {}
  artists = list(Artist.query.filter(Artist.name.ilike(f"%{search_term}%")).all())
  search_results["count"] = len(artists)
  search_results["data"] = []

  for artist in artists:
    each_artist = {
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": len(list(filter(lambda x: x.start_time > datetime.now(), artist.shows)))
    }
    search_results["data"].append(each_artist)

  return render_template('pages/search_artists.html', results=search_results, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  artist = Artist.query.get(artist_id)
  setattr(artist, "genres", artist.genres.split(", "))
  today = datetime.now()

  # get information about upcoming shows
  upcoming_shows_query = db.session.query(Shows).join(Venue).filter(Shows.artist_id==artist_id).filter(Shows.start_time>today).all()
  upcoming_shows = []
  for show in upcoming_shows_query:
    info = {"venue_name": show.venues.name, "venue_id": show.venues.id, "venue_image_link": show.venues.image_link, "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M:%S")}
    upcoming_shows.append(info)
  setattr(artist, "upcoming_shows", upcoming_shows)    
  setattr(artist,"upcoming_shows_count", len(upcoming_shows))

  # get information about past shows
  past_shows_query = db.session.query(Shows).join(Venue).filter(Shows.artist_id==artist_id).filter(Shows.start_time<today).all()
  past_shows = []
  for show in past_shows_query:
    info = {"venue_name": show.venues.name, "venue_id": show.venues.id, "venue_image_link": show.venues.image_link, "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M:%S")}
    past_shows.append(info)
  setattr(artist, "past_shows", past_shows)
  setattr(artist,"past_shows_count", len(past_shows))

  return render_template('pages/show_artist.html', artist=artist)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  # TODO: populate form with fields from artist with ID <artist_id>
  form = ArtistForm(request.form)
  data = {}
  artist = Artist.query.get(artist_id)

  data = {
    "id": artist.id,
    "name": artist.name,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "genres": artist.genres,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "website_link": artist.website_link
  }
  form.name.data = data['name']
  form.city.data = data['city']
  form.state.data = data['state']
  form.phone.data = data['phone']
  form.genres.data = data['genres']
  form.facebook_link.data = data['facebook_link']
  form.seeking_venue.data = data['seeking_venue']
  form.seeking_description.data = data['seeking_description']
  form.image_link.data = data['image_link']

  return render_template('forms/edit_artist.html', form=form, artist=data)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  form = ArtistForm(request.form)
  edit_artist = Artist.query.get(artist_id)
  if form.validate():
    try:
      edit_artist.name = form.name.data
      edit_artist.city = form.city.data
      edit_artist.state = form.state.data
      edit_artist.phone = form.phone.data
      edit_artist.genres = " ".join(form.genres.data)
      edit_artist.image_link = form.image_link.data
      edit_artist.facebook_link = form.facebook_link.data
      edit_artist.website_link = form.website_link.data
      edit_artist.seeking_venue = form.seeking_venue.data
      edit_artist.seeking_description = form.seeking_description.data
      db.session.add(edit_artist)
      db.session.commit()
      # on successful db insert, flash success
      flash('Artist ' + request.form['name'] + ' was successfully updated!')

    except:
      db.session.rollback()
      # TODO: on unsuccessful db insert, flash an error instead.
      # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
      # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be edited.')
      print(sys.exc_info())
    
    finally:
      db.session.close()
  else:
    flash(form.errors)
    flash('An error occurred. Artist ' + request.form['name'] +  ' could not be edited. Please check your form data and try again')
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  # TODO: populate form with values from venue with ID <venue_id>
  form = VenueForm(request.form)
  data = {}
  venue = Venue.query.get(venue_id)

  data = {
    "id": venue.id,
    "name": venue.name,
    "city": venue.city,
    "state": venue.state,
    "address": venue.address,
    "phone": venue.phone,
    "genres": venue.genre,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "website_link": venue.website_link
  }
  form.name.data = data['name']
  form.city.data = data['city']
  form.state.data = data['state']
  form.address.data = data['address']
  form.phone.data = data['phone']
  form.genres.data = data['genres']
  form.facebook_link.data = data['facebook_link']
  form.seeking_talent.data = data['seeking_talent']
  form.seeking_description.data = data['seeking_description']
  form.image_link.data = data['image_link']

  return render_template('forms/edit_venue.html', form=form, venue=data)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  form = VenueForm(request.form)
  edit_venue = Venue.query.get(venue_id)
  if form.validate():
    try:
      edit_venue.name = form.name.data
      edit_venue.city = form.city.data
      edit_venue.state = form.state.data
      edit_venue.phone = form.phone.data
      edit_venue.address = form.address.data
      edit_venue.genre = " ".join(form.genres.data)
      edit_venue.image_link = form.image_link.data
      edit_venue.facebook_link = form.facebook_link.data
      edit_venue.website_link = form.website_link.data
      edit_venue.seeking_talent = form.seeking_talent.data
      edit_venue.seeking_description = form.seeking_description.data
      db.session.add(edit_venue)
      db.session.commit()
      # on successful db insert, flash success
      flash('Venue ' + request.form['name'] + ' was successfully updated!')

    except:
      db.session.rollback()
      # TODO: on unsuccessful db insert, flash an error instead.
      # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
      # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be edited.')
      print(sys.exc_info())
    
    finally:
      db.session.close()
  else:
    flash(form.errors)
    flash('An error occurred. Venue ' + request.form['name'] +  ' could not be Edited. Please check your form data and try again')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = ArtistForm(request.form)
  if form.validate():
    try:
      name = form.name.data
      city = form.city.data
      state = form.state.data
      phone = form.phone.data
      genres = " ".join(form.genres.data)
      image_link = form.image_link.data
      facebook_link = form.facebook_link.data
      website_link = form.website_link.data
      seeking_venue = form.seeking_venue.data
      seeking_description = form.seeking_description.data
      create_artist = Artist(name = name, city = city, state = state, phone = phone, genres = genres, image_link = image_link, facebook_link = facebook_link, website_link = website_link, seeking_venue = seeking_venue, seeking_description = seeking_description)
      db.session.add(create_artist)
      db.session.commit()
      # on successful db insert, flash success
      flash('Artist ' + request.form['name'] + ' was successfully listed!')

    except:
      db.session.rollback()
      # TODO: on unsuccessful db insert, flash an error instead.
      # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
      # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
      print(sys.exc_info())
    finally:
      db.session.close()
  else:
    flash(form.errors)
    flash('An error occurred. Artist ' + request.form['name'] +  ' could not be listed. Please check your form data and try again')
  return render_template('pages/home.html')
  
#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  data = []
  try:
    shows = Shows.query.all()
    for show in shows:
      venue_id = show.venue_id
      artist_id = show.artist_id
      artist = Artist.query.get(artist_id)

      layout_shows = {
          "venue_id": venue_id,
          "venue_name": Venue.query.get(venue_id).name,
          "artist_id": artist_id,
          "artist_name": artist.name,
          "artist_image_link": artist.image_link,
          "start_time": str(show.start_time),
      }
      data.append(layout_shows)

  except:
    db.session.rollback()
    print(sys.exc_info())

  finally:
    return render_template("pages/shows.html", shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  form = ShowForm(request.form)
  if form.validate():
    try:
      new_show = Shows(
        artist_id=form.artist_id.data,
        venue_id=form.venue_id.data,
        start_time=form.start_time.data
        )
      db.session.add(new_show)
      db.session.commit()
      # on successful db insert, flash success
      flash('Show was successfully listed!')

    except:
      db.session.rollback()
      # TODO: on unsuccessful db insert, flash an error instead.
      flash('Show was not successfully listed.')
      # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
      print(sys.exc_info())
    finally:
      db.session.close()
  else:
    flash(form.errors)
    flash('An error occurred and your show could not be listed. Please check your form data and try again')
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
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
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
