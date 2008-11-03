/**
 * 
 */
package ee.olegus.fortran;

/**
 * @author olegus
 *
 */
public interface ASTVisitable {
	/**
	 * @param visitor
	 * @return TODO
	 * @return null or object that this visitable should be replaced with
	 */
	Object astWalk(ASTVisitor visitor);
}
