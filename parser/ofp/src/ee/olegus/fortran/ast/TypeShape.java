/**
 * 
 */
package ee.olegus.fortran.ast;

/**
 * @author olegus
 *
 */
public interface TypeShape {
	int getDimensions();
	Type getType();
	boolean hasAttribute(Attribute.Type type);
}
