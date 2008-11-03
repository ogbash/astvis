/**
 * 
 */
package ee.olegus.fortran;

import java.util.List;

import ee.olegus.fortran.ast.text.Locatable;
import ee.olegus.fortran.ast.text.Location;

/**
 * @author olegus
 *
 */
public class ASTUtils {

	public static Location calculateBlockLocation(List<? extends Object> stmts) {
		if (stmts.size()==0)
			return null;
		Location location = new Location();
		
		// calculate start 
		for(int i=0; i<stmts.size(); i++) {
			if(stmts.get(i) instanceof Locatable) {
				Locatable startStmt = (Locatable) stmts.get(i);
				if(startStmt.getLocation()!=null)
					location.start = startStmt.getLocation().start;
				break;
			}
		}		
				
		// calculate start 
		for(int i=stmts.size()-1; i>=0; i--) {
			if(stmts.get(i) instanceof Locatable) {
				Locatable endStmt = (Locatable) stmts.get(i);
				if(endStmt.getLocation()!=null)
					location.stop = endStmt.getLocation().stop;
				break;
			}
		}
		
		return location;
	}
}
