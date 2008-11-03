/**
 * 
 */
package ee.olegus.fortran;

import org.xml.sax.ContentHandler;
import org.xml.sax.SAXException;

/**
 * @author olegus
 *
 */
public interface XMLGenerator {
	void generateXML(ContentHandler handler) throws SAXException;
}
