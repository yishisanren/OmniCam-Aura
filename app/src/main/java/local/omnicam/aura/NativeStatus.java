package local.omnicam.aura;

/** Native activation evidence, also works when the firmware suppresses app logcat. */
public final class NativeStatus {
    private NativeStatus() {}
    public static native String snapshot();
}
