# Maintainer: Pat Wilson <pkgbuilds at patwsd dot com>
pkgname=cm4-dual-eth-fan-controld
pkgver=1.0
pkgrel=1
pkgdesc="Fan control daemon with systemd service for Waveshare CM4 Dual Gigabit Ethernet Base Board"
arch=('arm' 'armv7h' 'armv6h' 'aarch64')
url="https://github.com/patwil/cm4-dual-eth-fan-control.git"
license=('CC0-1.0')
depends=(
    'systemd'
    'python>3.12'
    'dtc'
    'uboot-tools'
    'sudo'
    'git'
    'make'
    'base-devel'
)
source=("${srcdir}/check_modules.py"
        "${srcdir}/cm4-dual-eth-fan-control.py"
        "${srcdir}/wiringpi_wrapper.py"
        "${srcdir}/cm4-dual-eth-fan-controld.service")
sha512sums=('8125efa8dd04cba7ba42d06bff4656e4af556248ddb8ab999a6b664ede98c2e5cbfd50a6674fefc684b8c39605acd202bee8011cc4bfa9ffab8e1702721181e2'
            '2a466fd434371706b4beb8e622b9fd0f570a319be3ac63f99affdd54f062d8cc60be8b6b851dfb8af146d39e68b535aedddc779cfdfe62f6095c793e1b86150d'
            '85fbc9e09abec856dffa3f21ac434494997cf4ef86dbb4704b42e1844e36d647f1893f29623c5bfb393b3f3396b325061b625cf0826384a4835a70f31a53b24f'
            'c3d07355af21f0b66310dcf2878e041adb7c5f8697358a5a6cafb1284a5e744cb26d0e2588ff6009d9416293a7675d6e36872629ad28a24f1c170e92f8c39536')

install=$pkgname.install

package() {
    cd "${srcdir}"
    
    # Install the Python files
    install -Dm755 "${srcdir}/cm4-dual-eth-fan-control.py" \
                    "${srcdir}/wiringpi_wrapper.py" \
                    "$pkgdir/usr/local/bin/cm4-dual-eth-fan-control.d"

    # Install the systemd unit
    install -Dm644 cm4-dual-eth-fan-controld.service \
        "$pkgdir/usr/lib/systemd/system/cm4-dual-eth-fan-controld.service"
}

