import java.nio.file.Files;
import java.nio.file.Paths;
import java.lang.reflect.Method;

/** Read-only decoder using this device's own SDK and JNI implementation. */
public final class DecodeConfig {
    public static void main(String[] args) throws Exception {
        System.load("/product/lib64/libOplusStringJNI.so");
        Class<?> type = Class.forName("com.oplus.ocs.camera.consumer.apsAdapter.config.OplusStringJNI");
        Object decoder = type.getConstructor().newInstance();
        Method need = type.getMethod("needGetString", byte[].class, int.class);
        Method decode = type.getMethod("getString", byte[].class, int.class, boolean.class, boolean.class);
        byte[] bytes = Files.readAllBytes(Paths.get(args[0]));
        String result = ((Boolean) need.invoke(decoder, bytes, bytes.length))
            ? (String) decode.invoke(decoder, bytes, bytes.length, false, false)
            : new String(bytes, "UTF-8");
        System.out.print(result);
    }
}
