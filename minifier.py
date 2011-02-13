import logging
import wsgiref.handlers
import os

from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.api import memcache

# Fix sys.path
import fix_path
fix_path.fix_sys_path()
import config
import jsmin
import cssmin


"""
Request Handler for Minified CSS
This allows to apply Templating and Minification to CSS Stylesheets.
"""
class CssMinifier( webapp.RequestHandler ):      
   def get( self, requestedCssFilename ):
      logging.debug("Requested CSS Path: "+requestedCssFilename);
      # Build the Path to the CSS and check if we already have rendered it and is sitting in Memcache ready to use
      cssPath = os.path.join( os.path.dirname( __file__ ), 'themes/%s/%s' % (config.theme, requestedCssFilename) );
      if ( not os.path.exists(cssPath) ):
         logging.error("CSS not found: "+cssPath);
         # Client Error 4xx - 404 Not Found
         util.setErrorResponse(self, 404);
         return;
      
      cssRenderingResult = None;
      # Check if Memcaching is enabled
      if ( config.memcaching ):
         cssRenderingResult = memcache.get(cssPath);
      
      # In case the Memcache didn't contain the CSS rendered
      if ( cssRenderingResult is None ):      
         logging.debug("Rendering CSS: "+cssPath);   
         # Render the CSS
         cssRenderingResult = template.render(cssPath, { 'config' : config });

         # Minify ONLY IF NOT Debugging
         if ( config.logging_level != logging.DEBUG ):
            logging.debug("Minifying CSS: "+requestedCssFilename);
            # Minify CSS
            cssRenderingResult = cssmin.minify(cssRenderingResult);
         
         # Save in Memcache
         memcache.set(cssPath, cssRenderingResult);
         
      # Setting Content-Type as "text/javascript"
      self.response.headers['Content-Type'] = 'text/css'
      logging.debug("Serving Minified CSS: "+cssPath);
      # Rendering the Result
      self.response.out.write( cssRenderingResult );


"""
Request Handler for "./js/*".
This allows to apply Templating and Minification to Javascript.
"""
class JSMinifier( webapp.RequestHandler ):      
   def get( self, requestedJsFilename ):
      logging.debug("Requested Javascript: "+requestedJsFilename);
      # Build the Path to the Javascript and check if we already have rendered it and is sitting in Memcache ready to use
      jsPath = os.path.join( os.path.dirname( __file__ ), 'themes/%s/%s' % (config.theme, requestedJsFilename) );
      if ( not os.path.exists(jsPath) ):
         logging.error("Javascript not found: "+jsPath);
         # Client Error 4xx - 404 Not Found
         util.setErrorResponse(self, 404);
         return;
      
      jsRenderingResult = None;
      if ( config.memcaching ):
         jsRenderingResult = memcache.get(jsPath);
      
      # In case the Memcache didn't contain the Javascript rendered
      if ( jsRenderingResult is None ):         
         logging.debug("Rendering Javascript: "+requestedJsFilename);   
         # Render the Javascript
         jsRenderingResult = template.render(jsPath, { 'config' : config });

         # Minify ONLY IF NOT Debugging
         if ( config.logging_level != logging.DEBUG ):
            logging.debug("Minifying Javascript: "+requestedJsFilename);
            # Minify Javascript
            jsRenderingResult = jsmin.jsmin(jsRenderingResult);
         
         # Save in Memcache
         memcache.set(jsPath, jsRenderingResult);
         
      # Setting Content-Type as "text/javascript"
      self.response.headers['Content-Type'] = 'application/javascript'
      logging.debug("Serving Minified Javascript: "+jsPath);
      # Rendering the Result
      self.response.out.write( jsRenderingResult );


# Creating a WSGI Application Handler
application = webapp.WSGIApplication([
                                      ( '(/.*\.js)$', JSMinifier ),
                                      ( '(/.*\.css)$', CssMinifier )
                                      ], debug=True )


def main():
   logging.getLogger().setLevel(config.logging_level);
   # Executing the WSGI Application
   wsgiref.handlers.CGIHandler().run( application )


if __name__ == "__main__":
   main()
