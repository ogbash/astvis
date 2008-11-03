/**
 * 
 */
package ee.olegus.fortran.ast;

import org.xml.sax.ContentHandler;
import org.xml.sax.SAXException;
import ee.olegus.fortran.ast.text.Location;

/**
 * Class that all statements should inherit from.
 * 
 * @author olegus
 *
 */
public abstract class Statement extends Construct {
	private Location location;

	public Location getLocation() {
		if(location==null)
			location = new Location();
		return location;
	}

	public void setLocation(Location location) {
		this.location = location;
	}
	
	public void generateXML(ContentHandler handler) throws SAXException {
		if(location!=null) {
			location.generateXML(handler);			
		}
	}	
}
