/**
 * 
 */
package ee.olegus.fortran.ast;

/**
 * Defined in scope.
 * 
 * @author olegus
 *
 */
public interface WithinScope {
	Scope getScope();
	String getName();
	String getFullName();
}
