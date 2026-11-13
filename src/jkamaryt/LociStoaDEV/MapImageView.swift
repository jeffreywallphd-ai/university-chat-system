import SwiftUI

struct MapImageView: View {
    var body: some View {
        Image("campus_map")
            .resizable()
            .aspectRatio(contentMode: .fit)
            .padding()
    }
}